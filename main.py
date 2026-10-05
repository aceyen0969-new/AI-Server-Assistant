import os
import asyncio

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from google import genai


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")


# =========================================================
# GEMINI
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# DISCORD BOT
# =========================================================

intents = discord.Intents.default()

intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# SETTINGS
# =========================================================

AI_CHANNEL_NAME = "ai-assistant"

GEMINI_MODEL = "gemini-3.8-flash"


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():

    print("----------------------------------------")
    print(f"Logged in as {bot.user}")
    print(f"Connected to {len(bot.guilds)} server(s)")
    print("----------------------------------------")

    try:

        synced = await bot.tree.sync()

        print(f"Synced {len(synced)} slash command(s)")

    except Exception as e:

        print("Command sync error:")
        print(e)


# =========================================================
# /PING
# =========================================================

@bot.tree.command(
    name="ping",
    description="Check if the bot is online."
)
async def ping(interaction: discord.Interaction):

    latency = round(bot.latency * 1000)

    await interaction.response.send_message(
        f"🏓 Pong! `{latency}ms`"
    )


# =========================================================
# /SERVERINFO
# =========================================================

@bot.tree.command(
    name="serverinfo",
    description="Show information about this Discord server."
)
async def serverinfo(interaction: discord.Interaction):

    guild = interaction.guild

    if guild is None:

        await interaction.response.send_message(
            "This command can only be used inside a server."
        )

        return

    embed = discord.Embed(
        title=f"📊 {guild.name}",
        description="Server information",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="👥 Members",
        value=f"{guild.member_count:,}",
        inline=True
    )

    embed.add_field(
        name="💬 Channels",
        value=str(len(guild.channels)),
        inline=True
    )

    embed.add_field(
        name="🎭 Roles",
        value=str(len(guild.roles)),
        inline=True
    )

    embed.add_field(
        name="🆔 Server ID",
        value=str(guild.id),
        inline=False
    )

    if guild.icon:

        embed.set_thumbnail(
            url=guild.icon.url
        )

    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# SEND LONG DISCORD MESSAGES
# =========================================================

async def send_long_message(
    channel: discord.abc.Messageable,
    text: str
):

    # Keep below Discord's 2000-character limit
    MAX_LENGTH = 1900

    while len(text) > MAX_LENGTH:

        chunk = text[:MAX_LENGTH]

        # Try to split at a paragraph
        split_position = chunk.rfind("\n\n")

        # If there isn't a good paragraph break,
        # try a normal line break
        if split_position < 500:
            split_position = chunk.rfind("\n")

        # If there isn't a good line break,
        # try to split at a space
        if split_position < 500:
            split_position = chunk.rfind(" ")

        # Last resort
        if split_position < 1:
            split_position = MAX_LENGTH

        await channel.send(
            text[:split_position].strip()
        )

        text = text[split_position:].strip()

    # Send the final part
    if text:

        await channel.send(text)


# =========================================================
# AI CHAT
# =========================================================

@bot.event
async def on_message(message: discord.Message):

    # Ignore bots
    if message.author.bot:
        return


    # -----------------------------------------------------
    # ONLY RESPOND IN #AI-ASSISTANT
    # -----------------------------------------------------

    if message.channel.name != AI_CHANNEL_NAME:

        await bot.process_commands(message)

        return


    # Get user's question
    question = message.content.strip()

    if not question:
        return


    # Make sure this is a server
    guild = message.guild

    if guild is None:
        return


    # =====================================================
    # DIRECT SERVER QUESTIONS
    # =====================================================

    member_questions = [
        "how many members",
        "how many people",
        "how many users",
        "member count",
        "user count",
        "how big is the server",
        "how many are in the server",
        "how many people are here",
        "how many members are here"
    ]

    question_lower = question.lower()

    if any(
        phrase in question_lower
        for phrase in member_questions
    ):

        await message.channel.send(
            f"👥 **{guild.name}** currently has "
            f"**{guild.member_count:,} members**."
        )

        return


    # =====================================================
    # SERVER CONTEXT FOR GEMINI
    # =====================================================

    server_context = f"""
You are the AI Server Assistant for a Discord server.

SERVER INFORMATION
------------------
Server name: {guild.name}
Member count: {guild.member_count}
Channel count: {len(guild.channels)}
Role count: {len(guild.roles)}

USER INFORMATION
----------------
User: {message.author.display_name}

USER QUESTION
-------------
{question}

INSTRUCTIONS
------------
Answer the user's question naturally and helpfully.

You know the server information listed above.

If the user asks about growing, improving, managing,
or organizing the server, use the available server
information when useful.

Give practical advice that a real Discord server owner
could actually use.

Keep responses reasonably concise.

For advice questions, aim for around 500-1000 words
maximum.

Use headings and bullet points when they make the answer
easier to read.

Do not invent server statistics or information that was
not provided.

You are an assistant for the server, not the server owner.

Do not claim that you performed an action on Discord
unless the bot actually performed that action.
"""


    # =====================================================
    # ASK GEMINI
    # =====================================================

    async with message.channel.typing():

        for attempt in range(3):

            try:

                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=server_context
                )

                answer = response.text

                if not answer:

                    answer = "I couldn't generate a response."


                # -------------------------------------------------
                # SEND LONG RESPONSES IN MULTIPLE MESSAGES
                # -------------------------------------------------

                await send_long_message(
                    message.channel,
                    answer
                )

                return


            except Exception as e:

                error_text = str(e)

                print("----------------------------------------")
                print(
                    f"Gemini attempt {attempt + 1} failed"
                )
                print(
                    f"Error type: {type(e).__name__}"
                )
                print(
                    f"Error: {error_text}"
                )
                print("----------------------------------------")


                # =================================================
                # DAILY QUOTA EXCEEDED
                # =================================================

                if (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                ):

                    await message.channel.send(
                        "⚠️ **Gemini's daily free-tier quota "
                        "has been reached.**\n\n"
                        "The AI should become available again "
                        "when the quota resets.\n\n"
                        "This is a Gemini API limit, not a "
                        "Discord bot error."
                    )

                    return


                # =================================================
                # TEMPORARY GEMINI SERVER ERROR
                # =================================================

                if (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                ):

                    if attempt < 2:

                        await asyncio.sleep(5)

                        continue


                # =================================================
                # OTHER ERROR
                # =================================================

                break


        # =================================================
        # ALL ATTEMPTS FAILED
        # =================================================

        await message.channel.send(
            "❌ Gemini couldn't process the request right now. "
            "Check the bot console for the error."
        )


# =========================================================
# SLASH COMMAND ERROR HANDLER
# =========================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    print("Command error:")
    print(error)

    if interaction.response.is_done():

        await interaction.followup.send(
            "❌ Something went wrong."
        )

    else:

        await interaction.response.send_message(
            "❌ Something went wrong."
        )


# =========================================================
# START BOT
# =========================================================

print("Starting AI Server Assistant...")

bot.run(DISCORD_TOKEN)
