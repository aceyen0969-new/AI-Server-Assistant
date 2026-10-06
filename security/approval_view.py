import discord

from security.approval import (
    approve_request,
    cancel_request,
    get_approval_request
)

from security.actions import (
    ActionRequest,
    can_execute_after_approval
)


class ApprovalView(discord.ui.View):

    def __init__(
        self,
        request_id: str,
        allowed_user_id: int,
        guild: discord.Guild,
        timeout: float = 300
    ):
        super().__init__(timeout=timeout)

        self.request_id = request_id
        self.allowed_user_id = allowed_user_id
        self.guild = guild

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

        action_request = ActionRequest(
            action=request.action,
            target_id=request.target_id,
            target_name=request.target_name,
            reason=request.reason,
            data=request.data
        )

        if not can_execute_after_approval(action_request):
            await interaction.response.edit_message(
                content=(
                    "⛔ **Action blocked.**\n\n"
                    "The safety policy no longer allows "
                    "this action to execute."
                ),
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

        try:
            if request.action == "move_channel":
                await self.execute_move_channel(
                    interaction,
                    request
                )
                return

            await interaction.response.edit_message(
                content=(
                    f"✅ **{request.action} approved.**\n\n"
                    "⚠️ An executor for this action has not "
                    "been implemented yet."
                ),
                embed=None,
                view=None
            )

        except discord.Forbidden:
            await interaction.response.edit_message(
                content=(
                    "❌ **Action failed.**\n\n"
                    "The bot does not have permission to perform "
                    "this Discord action."
                ),
                embed=None,
                view=None
            )

        except discord.HTTPException as e:
            await interaction.response.edit_message(
                content=(
                    "❌ **Discord rejected the action.**\n\n"
                    f"`{e}`"
                ),
                embed=None,
                view=None
            )

        except Exception as e:
            print("Action execution error:")
            print(e)

            await interaction.response.edit_message(
                content=(
                    "❌ **Action execution failed.**\n\n"
                    "Check the bot console for details."
                ),
                embed=None,
                view=None
            )

    async def execute_move_channel(
        self,
        interaction: discord.Interaction,
        request
    ):
        channel = self.guild.get_channel(
            request.target_id
        )

        if channel is None:
            await interaction.response.edit_message(
                content=(
                    "❌ **Channel no longer exists.**\n\n"
                    "The action was approved, but the target "
                    "could not be found."
                ),
                embed=None,
                view=None
            )
            return

        new_category_id = request.data.get(
            "new_category_id"
        )

        new_category = self.guild.get_channel(
            new_category_id
        )

        if not isinstance(
            new_category,
            discord.CategoryChannel
        ):
            await interaction.response.edit_message(
                content=(
                    "❌ **Destination category is invalid.**\n\n"
                    "The channel was not moved."
                ),
                embed=None,
                view=None
            )
            return

        if channel.category_id == new_category.id:
            await interaction.response.edit_message(
                content=(
                    "⚠️ **No change needed.**\n\n"
                    f"`{channel.name}` is already inside "
                    f"`{new_category.name}`."
                ),
                embed=None,
                view=None
            )
            return

        old_category_name = (
            channel.category.name
            if channel.category
            else "No Category"
        )

        await channel.edit(
            category=new_category,
            reason=(
                f"AI Server Assistant approved by "
                f"{interaction.user}"
            )
        )

        embed = discord.Embed(
            title="✅ Channel Moved",
            description=(
                f"**Channel:** {channel.mention}\n"
                f"**From:** `{old_category_name}`\n"
                f"**To:** `{new_category.name}`\n"
                f"**Reason:** {request.reason}"
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
