import os
import asyncio

import discord
from dotenv import load_dotenv
from google import genai

from utils.messages import send_long_message


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# SETTINGS
# =========================================================

AI_CHANNEL_NAME = "ai-assistant"

GEMINI_MODEL = "gemini-3.8-flash"


# =========================================================
# GEMINI CLIENT
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:

    raise RuntimeError(
        "GEMINI_API_KEY is missing from .env"
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# SETUP
# =========================================================

async def setup(bot):

    @bot.event
    async def on_message(message: discord.Message):

        # -------------------------------------------------
        # IGNORE BOTS
        # -------------------------------------------------

        if message.author.bot:
            return


        # -------------------------------------------------
        # ONLY RESPOND IN AI-ASSISTANT
        # -------------------------------------------------

        if message.channel.name != AI_CHANNEL_NAME:

            await bot.process_commands(message)

            return


        question = message.content.strip()

        if not question:
            return


        # -------------------------------------------------
        # SERVER CHECK
        # -------------------------------------------------

        guild = message.guild

        if guild is None:
            return


        # =================================================
        # DIRECT MEMBER QUESTIONS
        # =================================================

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
                f"👥 **{guild.name}** currently "
                f"has **{guild.member_count:,} "
                f"members**."
            )

            return


        # =================================================
        # BUILD CHANNEL STRUCTURE
        # =================================================

        channel_structure = []


        for category in guild.categories:

            channel_names = []


            for channel in category.channels:

                if isinstance(
                    channel,
                    discord.TextChannel
                ):

                    channel_names.append(
                        f"#{channel.name}"
                    )


                elif isinstance(
                    channel,
                    discord.VoiceChannel
                ):

                    channel_names.append(
                        f"🔊 {channel.name}"
                    )


            channel_structure.append(
                f"{category.name}: "
                + ", ".join(channel_names)
            )


        # =================================================
        # UNCATEGORIZED CHANNELS
        # =================================================

        uncategorized = []


        for channel in guild.channels:

            if channel.category is None:

                if isinstance(
                    channel,
                    discord.TextChannel
                ):

                    uncategorized.append(
                        f"#{channel.name}"
                    )


                elif isinstance(
                    channel,
                    discord.VoiceChannel
                ):

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


        # =================================================
        # SERVER CONTEXT
        # =================================================

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


        # =================================================
        # ASK GEMINI
        # =================================================

        async with message.channel.typing():

            for attempt in range(3):

                try:

                    response = client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=server_context
                    )


                    answer = response.text


                    if not answer:

                        answer = (
                            "I couldn't generate "
                            "a response."
                        )


                    await send_long_message(
                        message.channel,
                        answer
                    )

                    return


                except Exception as e:

                    error_text = str(e)


                    print(
                        "----------------------------------------"
                    )

                    print(
                        f"Gemini attempt "
                        f"{attempt + 1} failed"
                    )

                    print(
                        f"Error type: "
                        f"{type(e).__name__}"
                    )

                    print(
                        f"Error: {error_text}"
                    )

                    print(
                        "----------------------------------------"
                    )


                    # =====================================
                    # DAILY QUOTA
                    # =====================================

                    if (
                        "429" in error_text
                        or
                        "RESOURCE_EXHAUSTED"
                        in error_text
                    ):

                        await message.channel.send(
                            "⚠️ **Gemini's daily "
                            "free-tier quota has "
                            "been reached.**\n\n"
                            "The AI should become "
                            "available again when "
                            "the quota resets.\n\n"
                            "This is a Gemini API "
                            "limit, not a Discord "
                            "bot error."
                        )

                        return


                    # =====================================
                    # TEMPORARY SERVER ERROR
                    # =====================================

                    if (
                        "503" in error_text
                        or
                        "UNAVAILABLE"
                        in error_text
                    ):

                        if attempt < 2:

                            await asyncio.sleep(5)

                            continue


                    break


            # =============================================
            # ALL ATTEMPTS FAILED
            # =============================================

            await message.channel.send(
                "❌ Gemini couldn't process "
                "the request right now. "
                "Check the bot console "
                "for the error."
            )
