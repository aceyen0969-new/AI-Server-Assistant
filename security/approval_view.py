import discord

from security.approval import (
    approve_request,
    cancel_request,
    get_approval_request
)


class ApprovalView(discord.ui.View):
    def __init__(
        self,
        request_id: str,
        allowed_user_id: int,
        timeout: float = 300
    ):
        super().__init__(timeout=timeout)

        self.request_id = request_id
        self.allowed_user_id = allowed_user_id

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != self.allowed_user_id:
            await interaction.response.send_message(
                "⛔ You are not authorized to approve this action.",
                ephemeral=True
            )
            return False

        return True

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success,
        emoji="✅"
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        request = get_approval_request(
            self.request_id
        )

        if request is None:
            await interaction.response.edit_message(
                content="❌ This approval request no longer exists.",
                embed=None,
                view=None
            )
            return

        if request.cancelled:
            await interaction.response.edit_message(
                content="❌ This request has already been cancelled.",
                embed=None,
                view=None
            )
            return

        if request.approved:
            await interaction.response.edit_message(
                content="⚠️ This request has already been approved.",
                embed=None,
                view=None
            )
            return

        success = approve_request(
            self.request_id
        )

        if not success:
            await interaction.response.edit_message(
                content="❌ This request could not be approved.",
                embed=None,
                view=None
            )
            return

        embed = discord.Embed(
            title="✅ Action Approved",
            description=(
                f"**Action:** `{request.action}`\n"
                f"**Target:** {request.target_name or 'Unknown'}\n"
                f"**Reason:** {request.reason or 'No reason provided.'}"
            ),
            color=discord.Color.green()
        )

        embed.set_footer(
            text=f"Approved by {interaction.user}"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        emoji="❌"
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        request = get_approval_request(
            self.request_id
        )

        if request is None:
            await interaction.response.edit_message(
                content="❌ This approval request no longer exists.",
                embed=None,
                view=None
            )
            return

        if request.approved:
            await interaction.response.edit_message(
                content="⚠️ This request has already been approved.",
                embed=None,
                view=None
            )
            return

        if request.cancelled:
            await interaction.response.edit_message(
                content="⚠️ This request has already been cancelled.",
                embed=None,
                view=None
            )
            return

        success = cancel_request(
            self.request_id
        )

        if not success:
            await interaction.response.edit_message(
                content="❌ This request could not be cancelled.",
                embed=None,
                view=None
            )
            return

        embed = discord.Embed(
            title="❌ Action Cancelled",
            description=(
                f"**Action:** `{request.action}`\n"
                f"**Target:** {request.target_name or 'Unknown'}\n"
                f"**Reason:** {request.reason or 'No reason provided.'}"
            ),
            color=discord.Color.red()
        )

        embed.set_footer(
            text=f"Cancelled by {interaction.user}"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True