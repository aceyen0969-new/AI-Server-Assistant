import os
import asyncio
import re

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
# ORGANIZATION VIEW
# =========================================================

class OrganizationView(discord.ui.View):

    def __init__(
        self,
        author_id: int,
        guild: discord.Guild,
        proposal: str
    ):

        super().__init__(timeout=120)

        self.author_id = author_id
        self.guild = guild
        self.proposal = proposal


    # =====================================================
    # USER CHECK
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

        # Disable buttons immediately

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            view=self
        )


        # =================================================
        # PERMISSION CHECK
        # =================================================

        me = self.guild.me

        if me is None:

            await interaction.followup.send(
                "❌ I couldn't verify my permissions."
            )

            return


        if not me.guild_permissions.manage_channels:

            await interaction.followup.send(
                "❌ I need the **Manage Channels** "
                "permission to apply this organization."
            )

            return


        # =================================================
        # REFRESH SERVER DATA
        # =================================================

        try:

            await self.guild.fetch_channels()

        except Exception as e:

            print(
                "Failed to refresh channels:"
            )

            print(e)

            await interaction.followup.send(
                "❌ I couldn't refresh the server's "
                "channel information."
            )

            return


        # =================================================
        # FIND CHANNELS FROM PROPOSAL
        # =================================================

        current_channels = {
            channel.name.lower(): channel
            for channel in self.guild.channels
        }


        # =================================================
        # EXTRACT CHANNEL NAMES
        # =================================================

        proposed_channels = re.findall(
            r"#([a-zA-Z0-9_\-]+)",
            self.proposal
        )


        if not proposed_channels:

            await interaction.followup.send(
                "⚠️ I couldn't safely identify any "
                "channels in the proposal.\n\n"
                "No changes were made."
            )

            return


        # Remove duplicates while preserving order

        unique_channels = []

        for name in proposed_channels:

            if name.lower() not in [
                existing.lower()
                for existing in unique_channels
            ]:

                unique_channels.append(name)


        # =================================================
        # SAFETY CHECK
        # =================================================

        valid_channels = []

        missing_channels = []

        for name in unique_channels:

            channel = current_channels.get(
                name.lower()
            )

            if channel is None:

                missing_channels.append(name)

            else:

                valid_channels.append(channel)


        # =================================================
        # NOTHING VALID
        # =================================================

        if not valid_channels:

            await interaction.followup.send(
                "⚠️ None of the channels in the AI "
                "proposal could be safely matched "
                "to the current server.\n\n"
                "No changes were made."
            )

            return


        # =================================================
        # IMPORTANT SAFETY LIMIT
        # =================================================

        if len(valid_channels) > 50:

            await interaction.followup.send(
                "⚠️ The proposal contains too many "
                "channels to safely modify at once.\n\n"
                "No changes were made."
            )

            return


        # =================================================
        # APPLY ORGANIZATION
        # =================================================

        moved = 0
        failed = 0

        for channel in valid_channels:

            try:

                # -------------------------------------------------
                # We currently only move channels that are already
                # represented in the proposal.
                #
                # We do NOT delete or rename anything.
                # -------------------------------------------------

                if channel.category is not None:

                    # Already categorized.
                    # Leave it alone for now.
                    continue


                # -------------------------------------------------
                # No automatic category creation yet.
                #
                # This version safely handles the first step:
                # organizing uncategorized channels is prepared,
                # but category selection still needs structured AI
                # data before we move anything.
                # -------------------------------------------------

                failed += 1

            except Exception as e:

                print(
                    f"Failed to process #{channel.name}:"
                )

                print(e)

                failed += 1


        # =================================================
        # RESULT
        # =================================================

        if moved == 0:

            await interaction.followup.send(
                "⚠️ **Confirmation received.**\n\n"
                "I verified the proposal and my "
                "permissions, but I couldn't safely "
                "determine the exact target categories "
                "from the AI's text proposal.\n\n"
                "🛡️ **No channels were changed.**\n\n"
                "The next improvement will make the AI "
                "return structured channel-to-category "
                "instructions so Confirm can safely "
                "apply them."
            )

            return


        result = (
            f"✅ **Organization applied.**\n\n"
            f"Moved: **{moved}** channel(s)\n"
            f"Failed: **{failed}** channel(s)"
        )


        if missing_channels:

            result += (
                "\n\n⚠️ Channels no longer found:\n"
                + "\n".join(
                    f"• #{name}"
                    for name in missing_channels
                )
            )


        await interaction.followup.send(
            result
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
        # PERMISSION CHECK
        # =================================================

        me = guild.me

        if me is None:

            await interaction.response.send_message(
                "❌ I couldn't verify my permissions."
            )

            return


        if not me.guild_permissions.manage_channels:

            await interaction.response.send_message(
                "❌ I need the **Manage Channels** "
                "permission to organize channels."
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
2. Do NOT invent existing channels.
3. Do NOT rename channels.
4. Do NOT delete channels.
5. Use the exact existing channel names.
6. You may suggest existing categories.
7. Clearly mark newly suggested categories as PROPOSED.
8. Do not suggest unnecessary changes.
9. Keep the organization practical.
10. Clearly distinguish the current organization
    from the proposed organization.

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
        # DEFER
        # =================================================

        await interaction.response.defer()


        # =================================================
        # GEMINI
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


                # =================================================
                # EMBED
                # =================================================

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


                # =================================================
                # BUTTONS
                # =================================================

                view = OrganizationView(
                    author_id=interaction.user.id,
                    guild=guild,
                    proposal=answer
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


            # =================================================
            # ERROR
            # =================================================

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



            # =========================================================
            # QUOTA
            # =========================================================

            if (
                "429" in error_text
                or
                "RESOURCE_EXHAUSTED" in error_text
            ):

                # ---------------------------------------------
                # Get retry time from Gemini error
                # ---------------------------------------------

                import re

                retry_seconds = None

                match = re.search(
                    r"retryDelay.*?(\d+)s",
                    error_text
                )

                if match:

                    retry_seconds = int(
                        match.group(1)
                    )


                # ---------------------------------------------
                # Convert seconds into readable time
                # ---------------------------------------------

                if retry_seconds is not None:

                    days = retry_seconds // 86400

                    hours = (
                        retry_seconds % 86400
                    ) // 3600

                    minutes = (
                        retry_seconds % 3600
                    ) // 60

                    seconds = (
                        retry_seconds % 60
                    )


                    time_parts = []


                    if days:
                        time_parts.append(
                            f"{days}d"
                        )


                    if hours:
                        time_parts.append(
                            f"{hours}h"
                        )


                    if minutes:
                        time_parts.append(
                            f"{minutes}m"
                        )


                    if seconds:
                        time_parts.append(
                            f"{seconds}s"
                        )


                    reset_time = " ".join(
                        time_parts
                    )


                else:

                    reset_time = (
                        "unknown"
                    )


                # ---------------------------------------------
                # Terminal
                # ---------------------------------------------

                print(
                    "⚠️ GEMINI QUOTA EXCEEDED"
                )

                print(
                    f"⏳ Estimated quota reset: "
                    f"{reset_time}"
                )

                print(
                    "----------------------------------------"
                )


                # ---------------------------------------------
                # Discord
                # ---------------------------------------------

                await interaction.followup.send(
                    "⚠️ **Gemini's daily free-tier "
                    "quota has been reached.**\n\n"
                    f"⏳ **Estimated reset in: "
                    f"{reset_time}**\n\n"
                    "The bot will be able to use Gemini "
                    "again after the quota resets."
                )

                return

                # =================================================
                # 503
                # =================================================

                if (
                    "503" in error_text
                    or
                    "UNAVAILABLE"
                    in error_text
                ):

                    if attempt < 2:

                        print(
                            "⚠️ GEMINI TEMPORARILY "
                            "UNAVAILABLE"
                        )

                        print(
                            "Retrying in 5 seconds..."
                        )

                        await asyncio.sleep(5)

                        continue


                    break


                break


        # =================================================
        # FAILED
        # =================================================

        await interaction.followup.send(
            "❌ Gemini is currently unavailable after "
            "multiple attempts.\n\n"
            "The Discord bot itself is working. "
            "Please try `/organize` again later."
        )