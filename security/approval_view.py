import discord

from security.approval import (
    approve_request,
    cancel_request,
    get_approval_request,
)

from security.actions import (
    ActionRequest,
    can_execute_after_approval,
)

from ai.action_executor import execute_action


class ApprovalView(discord.ui.View):

    def __init__(
        self,
        request_id: str,
        allowed_user_id: int,
        guild: discord.Guild,
        timeout: float = 300,
    ):
        super().__init__(timeout=timeout)

        self.request_id = request_id
        self.allowed_user_id = allowed_user_id
        self.guild = guild

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.user.id != self.allowed_user_id:
            await interaction.response.send_message(
                "You are not authorized to approve this action.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success,
        emoji="✅",
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        request = get_approval_request(
            self.request_id
        )

        if request is None:
            await interaction.response.edit_message(
                content="This approval request no longer exists.",
                embed=None,
                view=None,
            )
            return

        if request.cancelled:
            await interaction.response.edit_message(
                content="This request has already been cancelled.",
                embed=None,
                view=None,
            )
            return

        if request.approved:
            await interaction.response.edit_message(
                content="This request has already been approved.",
                embed=None,
                view=None,
            )
            return

        action_request = ActionRequest(
            action=request.action,
            target_id=request.target_id,
            target_name=request.target_name,
            reason=request.reason,
            data=request.data,
        )

        if not can_execute_after_approval(
            action_request
        ):
            await interaction.response.edit_message(
                content=(
                    "Action blocked.\n\n"
                    "The security policy no longer "
                    "allows this action."
                ),
                embed=None,
                view=None,
            )
            return

        success = approve_request(
            self.request_id
        )

        if not success:
            await interaction.response.edit_message(
                content=(
                    "This request could not be approved."
                ),
                embed=None,
                view=None,
            )
            return

        await self.execute_approved_action(
            interaction,
            request,
        )

    async def execute_approved_action(
        self,
        interaction: discord.Interaction,
        request,
    ):
        """Execute an approved action using the central executor."""

        action = {
            "action": request.action,
            **request.data,
        }

        success = await execute_action(
            self.guild,
            action,
        )

        if not success:

            await interaction.response.edit_message(
                content=(
                    "The action was approved, but Discord "
                    "could not complete it.\n\n"
                    "Check the bot's permissions and "
                    "make sure the target still exists."
                ),
                embed=None,
                view=None,
            )

            return

        if request.action == "move_channel":

            channel_id = request.data.get(
                "channel_id"
            )

            category_id = request.data.get(
                "category_id"
            )

            channel = self.guild.get_channel(
                channel_id
            )

            category = self.guild.get_channel(
                category_id
            )

            if channel is None:
                await interaction.response.edit_message(
                    content=(
                        "The channel was moved, "
                        "but it could no longer be found."
                    ),
                    embed=None,
                    view=None,
                )
                return

            category_name = (
                category.name
                if isinstance(
                    category,
                    discord.CategoryChannel,
                )
                else "Unknown Category"
            )

            embed = discord.Embed(
                title="Channel Moved",
                description=(
                    f"**Channel:** {channel.mention}\n"
                    f"**To:** `{category_name}`\n"
                    f"**Reason:** {request.reason}"
                ),
                color=discord.Color.green(),
            )

            embed.set_footer(
                text=f"Approved by {interaction.user}"
            )

            await interaction.response.edit_message(
                embed=embed,
                view=None,
            )

            return

        await interaction.response.edit_message(
            content=(
                f"The action `{request.action}` "
                "was approved and executed."
            ),
            embed=None,
            view=None,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        emoji="❌",
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        request = get_approval_request(
            self.request_id
        )

        if request is None:
            await interaction.response.edit_message(
                content="This approval request no longer exists.",
                embed=None,
                view=None,
            )
            return

        if request.approved:
            await interaction.response.edit_message(
                content="This request has already been approved.",
                embed=None,
                view=None,
            )
            return

        if request.cancelled:
            await interaction.response.edit_message(
                content="This request has already been cancelled.",
                embed=None,
                view=None,
            )
            return

        success = cancel_request(
            self.request_id
        )

        if not success:
            await interaction.response.edit_message(
                content="This request could not be cancelled.",
                embed=None,
                view=None,
            )
            return

        await interaction.response.edit_message(
            content="Action cancelled.",
            view=None,
        )