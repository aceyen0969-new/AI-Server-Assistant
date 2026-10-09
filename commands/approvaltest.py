import uuid

import discord
from discord import app_commands

from security.approval import create_approval_request
from security.approval_view import ApprovalView


async def setup(bot):
    @bot.tree.command(
        name="approval-test",
        description="Test the AI channel-rename approval workflow.",
    )
    @app_commands.describe(
        target="The channel to rename.",
        new_name="The new name for the test channel.",
        reason="Why the rename was requested.",
    )
    async def approval_test(
        interaction: discord.Interaction,
        target: discord.TextChannel,
        new_name: str,
        reason: str,
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        if target.guild.id != guild.id:
            await interaction.response.send_message(
                "The target channel must belong to this server.",
                ephemeral=True,
            )
            return

        new_name = new_name.strip()

        if not new_name or len(new_name) > 100:
            await interaction.response.send_message(
                "The new channel name must be between 1 and 100 characters.",
                ephemeral=True,
            )
            return

        if target.name == new_name:
            await interaction.response.send_message(
                "The channel already has that name.",
                ephemeral=True,
            )
            return

        request_id = str(uuid.uuid4())

        create_approval_request(
            request_id=request_id,
            action="rename_channel",
            target_id=target.id,
            target_name=target.name,
            reason=reason,
            data={
                "channel_id": target.id,
                "new_name": new_name,
            },
            guild_id=guild.id,
            approver_id=guild.owner_id,
        )

        embed = discord.Embed(
            title="🛡️ AI Action Request",
            description=(
                "**Action:** `rename_channel`\n"
                f"**Target:** {target.mention}\n"
                f"**New name:** `{new_name}`\n"
                f"**Reason:** {reason}\n\n"
                "This action requires approval."
            ),
            color=discord.Color.orange(),
        )

        embed.set_footer(
            text="Only the server owner can approve this request."
        )

        view = ApprovalView(
            request_id=request_id,
            allowed_user_id=guild.owner_id,
            guild=guild,
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
        )