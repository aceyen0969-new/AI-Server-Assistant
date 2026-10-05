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
    description="Show basic information about this Discord server."
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
# /SERVERSTATS
# =========================================================

@bot.tree.command(
    name="serverstats",
    description="Show detailed statistics about this server."
)
async def serverstats(interaction: discord.Interaction):

    guild = interaction.guild

    if guild is None:

        await interaction.response.send_message(
            "This command can only be used inside a server."
        )

        return


    # -----------------------------------------------------
    # CHANNEL COUNTS
    # -----------------------------------------------------

    text_channels = len(guild.text_channels)

    voice_channels = len(guild.voice_channels)

    categories = len(guild.categories)

    total_channels = len(guild.channels)


    # -----------------------------------------------------
    # MEMBER COUNTS
    # -----------------------------------------------------

    total_members = guild.member_count or 0

    bot_count = sum(
        1
        for member in guild.members
        if member.bot
    )

    human_count = total_members - bot_count


    online_members = sum(
        1
        for member in guild.members
        if member.status != discord.Status.offline
    )


    # -----------------------------------------------------
    # ROLE COUNT
    # -----------------------------------------------------

    role_count = len(guild.roles) - 1

    if role_count < 0:
        role_count = 0


    # -----------------------------------------------------
    # EMBED
    # -----------------------------------------------------

    embed = discord.Embed(
        title=f"📊 {guild.name} Server Statistics",
        description="Detailed overview of your Discord server.",
        color=discord.Color.blurple()
    )


    embed.add_field(
        name="👥 Members",
        value=(
            f"Total: **{total_members:,}**\n"
            f"Humans: **{human_count:,}**\n"
            f"Bots: **{bot_count:,}**\n"
            f"Online: **{online_members:,}**"
        ),
        inline=True
    )


    embed.add_field(
        name="💬 Channels",
        value=(
            f"Total: **{total_channels:,}**\n"
            f"Text: **{text_channels:,}**\n"
            f"Voice: **{voice_channels:,}**\n"
            f"Categories: **{categories:,}**"
        ),
        inline=True
    )


    embed.add_field(
        name="🏗️ Structure",
        value=(
            f"Roles: **{role_count:,}**\n"
            f"Server ID: `{guild.id}`"
        ),
        inline=True
    )


    if guild.owner:

        embed.add_field(
            name="👑 Owner",
            value=guild.owner.mention,
            inline=False
        )


    if guild.icon:

        embed.set_thumbnail(
            url=guild.icon.url
        )


    embed.set_footer(
        text="AI Server Assistant • Server Analytics"
    )


    await interaction.response.send_message(
        embed=embed
    )


# =========================================================
# /CHANNELS
# =========================================================

@bot.tree.command(
    name="channels",
    description="Analyze the server's channel organization."
)
async def channels(interaction: discord.Interaction):

    guild = interaction.guild

    if guild is None:

        await interaction.response.send_message(
            "This command can only be used inside a server."
        )

        return


    # -----------------------------------------------------
    # CREATE CHANNEL STRUCTURE
    # -----------------------------------------------------

    categories = guild.categories

    uncategorized_text = []
    uncategorized_voice = []

    category_data = []


    # -----------------------------------------------------
    # CHECK CATEGORIES
    # -----------------------------------------------------

    for category in categories:

        text_channels = []
        voice_channels = []

        for channel in category.channels:

            if isinstance(channel, discord.TextChannel):

                text_channels.append(
                    f"#{channel.name}"
                )

            elif isinstance(channel, discord.VoiceChannel):

                voice_channels.append(
                    f"🔊 {channel.name}"
                )


        category_data.append(
            (
                category.name,
                text_channels,
                voice_channels
            )
        )


    # -----------------------------------------------------
    # FIND UNCATEGORIZED CHANNELS
    # -----------------------------------------------------

    for channel in guild.channels:

        if channel.category is not None:
            continue


        if isinstance(channel, discord.TextChannel):

            uncategorized_text.append(
                f"#{channel.name}"
            )


        elif isinstance(channel, discord.VoiceChannel):

            uncategorized_voice.append(
                f"🔊 {channel.name}"
            )


    # -----------------------------------------------------
    # CREATE EMBED
    # -----------------------------------------------------

    embed = discord.Embed(
        title=f"📋 {guild.name} Channel Structure",
        description="Current organization of your server channels.",
        color=discord.Color.blurple()
    )


    # -----------------------------------------------------
    # CATEGORY FIELDS
    # -----------------------------------------------------

    for category_name, text_channels, voice_channels in category_data:

        channel_list = []

        channel_list.extend(text_channels)
        channel_list.extend(voice_channels)


        if not channel_list:

            channel_list.append("No channels")


        channel_text = "\n".join(channel_list)


        # Discord embed fields have a 1024-character limit
        if len(channel_text) > 1000:

            channel_text = channel_text[:997] + "..."


        embed.add_field(
            name=f"📁 {category_name}",
            value=channel_text,
            inline=False
        )


    # -----------------------------------------------------
    # UNCATEGORIZED CHANNELS
    # -----------------------------------------------------

    uncategorized = []

    uncategorized.extend(uncategorized_text)
    uncategorized.extend(uncategorized_voice)


    if uncategorized:

        uncategorized_text_display = "\n".join(
            uncategorized
        )

        if len(uncategorized_text_display) > 1000:

            uncategorized_text_display = (
                uncategorized_text_display[:997]
                + "..."
            )


        embed.add_field(
            name="⚠️ Uncategorized",
            value=uncategorized_text_display,
            inline=False
        )

    else:

        embed.add_field(
            name="✅ Uncategorized",
            value="All channels are currently inside categories.",
            inline=False
        )


    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    embed.add_field(
        name="📊 Summary",
        value=(
            f"Categories: **{len(categories)}**\n"
            f"Text channels: **{len(guild.text_channels)}**\n"
            f"Voice channels: **{len(guild.voice_channels)}**"
        ),
        inline=False
    )


    embed.set_footer(
        text="AI Server Assistant • Channel Analyzer"
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

    MAX_LENGTH = 1900

    while len(text) > MAX_LENGTH:

        chunk = text[:MAX_LENGTH]

        split_position = chunk.rfind("\n\n")

        if split_position < 500:
            split_position = chunk.rfind("\n")

        if split_position < 500:
            split_position = chunk.rfind(" ")

        if split_position < 1:
            split_position = MAX_LENGTH

        await channel.send(
            text[:split_position].strip()
        )

        text = text[split_position:].strip()


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


    question = message.content.strip()

    if not question:
        return


    guild = message.guild

    if guild is None:
        return


    # =====================================================
    # DIRECT MEMBER QUESTIONS
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
    # BUILD CHANNEL STRUCTURE FOR GEMINI
    # =====================================================

    channel_structure = []


    for category in guild.categories:

        channel_names = []


        for channel in category.channels:

            if isinstance(channel, discord.TextChannel):

                channel_names.append(
                    f"#{channel.name}"
                )

            elif isinstance(channel, discord.VoiceChannel):

                channel_names.append(
                    f"🔊 {channel.name}"
                )


        channel_structure.append(
            f"{category.name}: "
            + ", ".join(channel_names)
        )


    # -----------------------------------------------------
    # UNCATEGORIZED CHANNELS
    # -----------------------------------------------------

    uncategorized = []


    for channel in guild.channels:

        if channel.category is None:

            if isinstance(channel, discord.TextChannel):

                uncategorized.append(
                    f"#{channel.name}"
                )

            elif isinstance(channel, discord.VoiceChannel):

                uncategorized.append(
                    f"🔊 {channel.name}"
                )


    if uncategorized:

        channel_structure.append(
            "UNCATEGORIZED: "
            + ", ".join(uncategorized)
        )


    channel_structure_text = "\n".join(
        channel_structure
    )


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
Text channels: {len(guild.text_channels)}
Voice channels: {len(guild.voice_channels)}
Categories: {len(guild.categories)}

CHANNEL STRUCTURE
-----------------
{channel_structure_text}

USER INFORMATION
----------------
User: {message.author.display_name}

USER QUESTION
-------------
{question}

INSTRUCTIONS
------------
Answer the user's question naturally and helpfully.

You know the server information and channel structure
listed above.

If the user asks about growing, improving, managing,
or organizing the server, use the actual server
information when useful.

If the user asks about channel organization, analyze
the actual channel names and categories provided above.

Give practical advice that a real Discord server owner
could actually use.

Keep responses reasonably concise.

Use headings and bullet points when they make the answer
easier to read.

Do not invent server statistics, channels, categories,
or information that was not provided.

You are an assistant for the server, not the server owner.

IMPORTANT:
You can currently ONLY provide advice.

Do not claim that you moved, renamed, deleted, created,
or modified anything on Discord.

Do not claim that you performed an action unless the bot
actually performed that action.
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
