import os
import asyncio

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
# CONFIRMATION VIEW
# =========================================================

class OrganizationView(discord.ui.View):

    def __init__(self, author_id: int):

        super().__init__(timeout=120)

        self.author_id = author_id


    # =====================================================
    # CHECK USER
    # =====================================================

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id != self.author_id:

            await interaction.response.send_message(
                "❌ Only the person who created this "
                "proposal can use these buttons.",
                ephemeral=True
            )

            return False

        return True


    # =====================================================
    # CONFIRM
    # =====================================================

    @discord.ui.button(
        label="Confirm",
        emoji="✅",
        style=discord.ButtonStyle.success
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # Disable both buttons

        for item in self.children:

            item.disabled = True


        await interaction.response.edit_message(
            view=self
        )


        await interaction.followup.send(
            "✅ **Proposal confirmed.**\n\n"
            "No channels have been changed yet.\n\n"
            "The next update will allow the bot to "
            "actually apply approved organization changes."
        )


    # =====================================================
    # CANCEL
    # =====================================================

    @discord.ui.button(
        label="Cancel",
        emoji="❌",
        style=discord.ButtonStyle.danger
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        for item in self.children:

            item.disabled = True


        await interaction.response.edit_message(
            view=self
        )


        await interaction.followup.send(
            "❌ **Organization proposal cancelled.**\n\n"
            "No changes were made to the server."
        )


    # =====================================================
    # TIMEOUT
    # =====================================================

    async def on_timeout(self):

        for item in self.children:

            item.disabled = True


# =========================================================
# SETUP
# =========================================================

async def setup(bot):

    @bot.tree.command(
        name="organize",
        description=(
            "Ask AI for a cleaner channel organization."
        )
    )
    async def organize(
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "This command can only be used inside "
                "a server."
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


            if channels:

                structure.append(
                    f"📁 {category.name}\n"
                    + "\n".join(
                        f"  {channel}"
                        for channel in channels
                    )
                )

            else:

                structure.append(
                    f"📁 {category.name}\n"
                    "  No channels"
                )


        # =================================================
        # UNCATEGORIZED CHANNELS
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
2. Do NOT invent existing channels.
3. Do NOT pretend proposed categories already exist.
4. Use the actual channel names when making suggestions.
5. Do not suggest unnecessary changes if the server is
   already organized well.
6. Consider what each channel appears to be used for based
   on its name.
7. Keep the proposal practical for a real Discord server.
8. Clearly distinguish proposed organization from the
   current organization.

FORMAT:

🧠 AI Organization Proposal

📁 CATEGORY NAME
#channel
#channel

📁 ANOTHER CATEGORY
#channel
🔊 voice-channel

💡 Why?
Brief explanation.

⚠️ No changes have been made yet.
"""


        # =================================================
        # DISCORD LOADING STATE
        # =================================================

        await interaction.response.defer()


        # =================================================
        # ASK GEMINI
        # =================================================

        for attempt in range(3):

            try:

                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt
                )


                answer = response.text


                if not answer:

                    answer = (
                        "I couldn't generate an "
                        "organization proposal."
                    )


                # =========================================
                # EMBED
                # =========================================

                embed = discord.Embed(
                    title="🧠 AI Organization Proposal",
                    description=answer[:4000],
                    color=discord.Color.blurple()
                )


                embed.set_footer(
                    text=(
                        "AI Server Assistant • "
                        "Review before confirming"
                    )
                )


                # =========================================
                # BUTTONS
                # =========================================

                view = OrganizationView(
                    author_id=interaction.user.id
                )


                await interaction.followup.send(
                    embed=embed,
                    view=view
                )


                print(
                    "----------------------------------------"
                )

                print(
                    "✅ ORGANIZE AI REQUEST SUCCESSFUL"
                )

                print(
                    f"Attempt: {attempt + 1}"
                )

                print(
                    "Confirmation buttons displayed."
                )

                print(
                    "----------------------------------------"
                )

                return


            # =============================================
            # ERROR
            # =============================================

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


                # =========================================
                # QUOTA
                # =========================================

                if (
                    "429" in error_text
                    or
                    "RESOURCE_EXHAUSTED"
                    in error_text
                ):

                    print()
                    print(
                        "⚠️ GEMINI QUOTA EXCEEDED"
                    )

                    print(
                        "The Gemini API free-tier quota "
                        "has been reached."
                    )

                    print(
                        "Wait for the quota to reset."
                    )

                    print(
                        "----------------------------------------"
                    )


                    await interaction.followup.send(
                        "⚠️ **Gemini's daily free-tier "
                        "quota has been reached.**\n\n"
                        "Try again after the quota resets."
                    )


                    return


                # =========================================
                # 503
                # =========================================

                if (
                    "503" in error_text
                    or
                    "UNAVAILABLE"
                    in error_text
                ):

                    if attempt < 2:

                        print()
                        print(
                            "⚠️ GEMINI TEMPORARILY "
                            "UNAVAILABLE"
                        )

                        print(
                            "Retrying in 5 seconds..."
                        )

                        print(
                            "----------------------------------------"
                        )


                        await asyncio.sleep(5)

                        continue


                    print()
                    print(
                        "❌ GEMINI STILL UNAVAILABLE"
                    )

                    print(
                        "All retry attempts failed."
                    )

                    print(
                        "----------------------------------------"
                    )

                    break


                # =========================================
                # OTHER ERROR
                # =========================================

                print()
                print(
                    "❌ UNKNOWN GEMINI ERROR"
                )

                print(
                    "----------------------------------------"
                )

                break


        # =================================================
        # ALL ATTEMPTS FAILED
        # =================================================

        await interaction.followup.send(
            "❌ Gemini is currently unavailable after "
            "multiple attempts.\n\n"
            "The Discord bot itself is working. "
            "Please try `/organize` again later."
        )