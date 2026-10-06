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
        """Execute an action after owner approval."""

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
                    content="The target channel no longer exists.",
                    embed=None,
                    view=None,
                )

                return

            if category is None:
                await interaction.response.edit_message(
                    content="The target category no longer exists.",
                    embed=None,
                    view=None,
                )

                return

            if not isinstance(
                category,
                discord.CategoryChannel,
            ):
                await interaction.response.edit_message(
                    content="The selected destination is not a category.",
                    embed=None,
                    view=None,
                )

                return

            if channel.category_id == category.id:
                await interaction.response.edit_message(
                    content=(
                        f"`{channel.name}` is already inside "
                        f"`{category.name}`."
                    ),
                    embed=None,
                    view=None,
                )

                return

            old_category_name = (
                channel.category.name
                if channel.category
                else "No Category"
            )

            try:
                await channel.edit(
                    category=category,
                    reason=(
                        "AI Server Assistant action "
                        f"approved by {interaction.user}"
                    ),
                )

            except discord.Forbidden:
                await interaction.response.edit_message(
                    content=(
                        "Discord denied the action. "
                        "Check the bot's Manage Channels permission."
                    ),
                    embed=None,
                    view=None,
                )

                return

            except discord.HTTPException as e:
                await interaction.response.edit_message(
                    content=(
                        f"Discord returned an error: `{e}`"
                    ),
                    embed=None,
                    view=None,
                )

                return

            embed = discord.Embed(
                title="Channel Moved",
                description=(
                    f"**Channel:** {channel.mention}\n"
                    f"**From:** `{old_category_name}`\n"
                    f"**To:** `{category.name}`\n"
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
                "does not have an approval executor yet."
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
            embed=None,
            view=None,
        )