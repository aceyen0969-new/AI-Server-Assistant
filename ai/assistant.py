import discord

from utils.messages import send_long_message
from ai.manager import ask_ai


AI_CHANNEL_NAME = "ai-assistant"

# =========================================================
# CONVERSATION MEMORY
# =========================================================

# Memory is separated by Discord channel.
#
# Example:
#
# {
#     123456789: [
#         {
#             "role": "user",
#             "content": "How can I improve my server?"
#         },
#         {
#             "role": "assistant",
#             "content": "You could improve..."
#         }
#     ]
# }

conversation_memory = {}

# Remember the last 20 messages
# = roughly 10 user/assistant exchanges.
MAX_HISTORY = 20


async def setup(bot):

    @bot.event
    async def on_message(message: discord.Message):

        # =================================================
        # IGNORE BOTS
        # =================================================

        if message.author.bot:
            return


        # =================================================
        # ONLY RESPOND IN AI CHANNEL
        # =================================================

        if message.channel.name != AI_CHANNEL_NAME:

            await bot.process_commands(message)

            return


        # =================================================
        # IGNORE DMS
        # =================================================

        guild = message.guild

        if guild is None:
            return


        # =================================================
        # GET QUESTION
        # =================================================

        question = message.content.strip()

        if not question:
            return


        # =================================================
        # DIRECT MEMBER COUNT QUESTIONS
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

CURRENT USER QUESTION
---------------------
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
        # GET CONVERSATION MEMORY
        # =================================================

        channel_id = message.channel.id

        if channel_id not in conversation_memory:

            conversation_memory[channel_id] = []


        history = conversation_memory[channel_id]


        # =================================================
        # ASK AI
        # =================================================

        async with message.channel.typing():

            result = await ask_ai(
                server_context,
                history
            )


        answer = result.get("answer")

        provider = result.get("provider")


        # =================================================
        # AI FAILURE
        # =================================================

        if not answer:

            await message.channel.send(
                "❌ **All AI providers are "
                "currently unavailable.**\n\n"
                "Gemini, OpenRouter, and Groq "
                "could not process the request."
            )

            return


        # =================================================
        # SAVE CONVERSATION
        # =================================================

        history.append(
            {
                "role": "user",
                "content": question
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


        # =================================================
        # LIMIT MEMORY
        # =================================================

        if len(history) > MAX_HISTORY:

            conversation_memory[channel_id] = (
                history[-MAX_HISTORY:]
            )


        # =================================================
        # SEND RESPONSE
        # =================================================

        await send_long_message(
            message.channel,
            answer
        )


        # =================================================
        # LOG PROVIDER
        # =================================================

        print("----------------------------------------")

        print(
            f"🤖 AI Provider used: {provider}"
        )

        print(
            f"🧠 Conversation memory: "
            f"{len(conversation_memory[channel_id])} messages"
        )

        print("----------------------------------------")