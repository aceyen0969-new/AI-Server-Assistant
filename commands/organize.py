import os

import discord
from dotenv import load_dotenv
from google import genai


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from .env"
    )


# =========================================================
# GEMINI
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)

GEMINI_MODEL = "gemini-3.8-flash"


# =========================================================
# SETUP
# =========================================================

async def setup(bot):

    @bot.tree.command(
        name="organize",
        description="Ask AI for a cleaner channel organization."
    )
    async def organize(interaction: discord.Interaction):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server."
            )

            return

        # =================================================
        # BUILD CHANNEL STRUCTURE
        # =================================================

        structure = []

        for category in guild.categories:

            channels = []

            for channel in category.channels:

                if isinstance(
                    channel,
                    discord.TextChannel
                ):

                    channels.append(
                        f"#{channel.name}"
                    )

                elif isinstance(
                    channel,
                    discord.VoiceChannel
                ):

                    channels.append(
                        f"🔊 {channel.name}"
                    )

            structure.append(
                f"📁 {category.name}\n"
                + "\n".join(
                    f"  {channel}"
                    for channel in channels
                )
            )

        # =================================================
        # UNCATEGORIZED
        # =================================================

        uncategorized = []

        for channel in guild.channels:

            if channel.category is not None:
                continue

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

            structure.append(
                "⚠️ UNCATEGORIZED\n"
                + "\n".join(
                    f"  {channel}"
                    for channel in uncategorized
                )
            )

        channel_structure = "\n\n".join(
            structure
        )

        # =================================================
        # AI PROMPT
        # =================================================

        prompt = f"""
You are an AI Discord Server Organization Assistant.

Analyze the actual Discord channel structure below.

SERVER:
{guild.name}

CURRENT CHANNEL STRUCTURE:
{channel_structure}

Your job is to suggest a cleaner organization.

IMPORTANT RULES:

1. Do NOT claim that you changed anything.
2. Do NOT invent channels that don't exist.
3. Do NOT invent categories unless you clearly label them
   as proposed categories.
4. Use the actual channel names when making suggestions.
5. Don't suggest unnecessary changes if the server is
   already organized well.
6. Consider what each channel appears to be used for based
   on its name.
7. Keep the proposal practical for a real Discord server.

FORMAT YOUR RESPONSE LIKE THIS:

🧠 AI Organization Proposal

📁 CATEGORY NAME
#channel
#channel

📁 ANOTHER CATEGORY
#channel
🔊 voice-channel

💡 Why?
Brief explanation of why this organization would be
better.

⚠️ No changes have been made yet.
"""


        # =================================================
        # ASK GEMINI
        # =================================================

        await interaction.response.defer()


        for attempt in range(3):

            try:

                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt
                )

                answer = response.text

                if not answer:

                    answer = (
                        "I couldn't generate an organization "
                        "proposal."
                    )

                embed = discord.Embed(
                    title="🧠 AI Organization Proposal",
                    description=answer[:4000],
                    color=discord.Color.blurple()
                )

                embed.set_footer(
                    text=(
                        "AI Server Assistant • "
                        "Suggestion only • No changes made"
                    )
                )

                await interaction.followup.send(
                    embed=embed
                )

                return


            except Exception as e:

                error_text = str(e)

                print(
                    "----------------------------------------"
                )

                print(
                    f"Organize AI attempt "
                    f"{attempt + 1} failed"
                )

                print(
                    f"Error: {error_text}"
                )

                print(
                    "----------------------------------------"
                )


                # =============================================
                # DAILY QUOTA
                # =============================================

                if (
                    "429" in error_text
                    or
                    "RESOURCE_EXHAUSTED" in error_text
                ):

                    await interaction.followup.send(
                        "⚠️ Gemini's daily free-tier quota "
                        "has been reached.\n\n"
                        "Try again after the quota resets."
                    )

                    return


                # =============================================
                # TEMPORARY 503 ERROR
                # =============================================

                if (
                    "503" in error_text
                    or
                    "UNAVAILABLE" in error_text
                ):

                    if attempt < 2:

                        import asyncio

                        await asyncio.sleep(5)

                        continue


                break


        # =============================================
        # ALL ATTEMPTS FAILED
        # =============================================

        await interaction.followup.send(
            "❌ Gemini is currently unavailable after "
            "multiple attempts.\n\n"
            "The bot itself is working. Try `/organize` "
            "again later."
        )

