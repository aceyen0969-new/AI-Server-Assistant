import uuid

import discord
from discord import app_commands

from security.approval import create_approval_request
from security.approval_view import ApprovalView


async def setup(bot):
    @bot.tree.command(
        name="approval-test",
        description="Test the AI action approval system."
    )
    @app_commands.describe(
        action="The action to test.",
        target="The target of the action.",
        reason="Why the action was requested."
    )
    async def approval_test(
        interaction: discord.Interaction,
        action: str,
        target: str,
        reason: str
    ):
        request_id = str(uuid.uuid4())

        create_approval_request(
            request_id=request_id,
            action=action,
            target_name=target,
            reason=reason
        )

        embed = discord.Embed(
            title="🛡️ AI Action Request",
            description=(
                f"**Action:** `{action}`\n"
                f"**Target:** {target}\n"
                f"**Reason:** {reason}\n\n"
                "⚠️ This action requires approval."
            ),
            color=discord.Color.orange()
        )

        embed.set_footer(
            text="Only the server owner can approve this request."
        )

        view = ApprovalView(
            request_id=request_id,
            allowed_user_id=interaction.guild.owner_id
        )

        await interaction.response.send_message(
            embed=embed,
            view=view
        )
