import uuid

import discord
from discord import app_commands

from ai.action_planner import plan_actions

from security.actions import (
    ActionRequest,
    evaluate_action,
)

from security.approval import (
    create_approval_request,
)

from security.approval_view import (
    ApprovalView,
)


async def setup(bot):

    @bot.tree.command(
        name="organize",
        description="Ask the AI to suggest a server organization change.",
    )
    @app_commands.describe(
        request="Describe the server organization change you want."
    )
    async def organize(
        interaction: discord.Interaction,
        request: str,
    ):
        await interaction.response.defer()

        guild = interaction.guild

        if guild is None:
            await interaction.followup.send(
                "This command can only be used inside a server."
            )
            return

        planned = await plan_actions(
            guild,
            request,
        )

        actions = planned.get(
            "actions",
            [],
        )

        if not actions:
            await interaction.followup.send(
                "I couldn't turn that request into a valid "
                "server organization action."
            )
            return

        created = 0

        for action in actions:

            action_type = action.get(
                "action"
            )

            # ========================================
            # MOVE CHANNEL
            # ========================================

            if action_type == "move_channel":

                channel_id = action.get(
                    "channel_id"
                )

                category_id = action.get(
                    "category_id"
                )

                channel = guild.get_channel(
                    channel_id
                )

                category = guild.get_channel(
                    category_id
                )

                if channel is None:
                    continue

                if category is None:
                    continue

                if not isinstance(
                    category,
                    discord.CategoryChannel,
                ):
                    continue

                if not isinstance(
                    channel,
                    (
                        discord.TextChannel,
                        discord.VoiceChannel,
                    ),
                ):
                    continue

                action_request = ActionRequest(
                    action="move_channel",
                    target_id=channel.id,
                    target_name=channel.name,
                    reason=request,
                    data={
                        "channel_id": channel.id,
                        "category_id": category.id,
                    },
                )

                decision = evaluate_action(
                    action_request
                )

                if not decision["allowed"] and not decision["requires_approval"]:
                    continue

                if not decision["requires_approval"]:
                    continue

                request_id = str(
                    uuid.uuid4()
                )

                create_approval_request(
                    request_id=request_id,
                    action="move_channel",
                    target_id=channel.id,
                    target_name=channel.name,
                    reason=request,
                    data={
                        "channel_id": channel.id,
                        "category_id": category.id,
                    },
                )

                embed = discord.Embed(
                    title="AI Organization Request",
                    description=(
                        f"**Action:** `move_channel`\n"
                        f"**Channel:** {channel.mention}\n"
                        f"**New Category:** `{category.name}`\n"
                        f"**Request:** {request}\n\n"
                        "This change requires server-owner approval."
                    ),
                    color=discord.Color.orange(),
                )

                embed.set_footer(
                    text="AI Server Assistant"
                )

                view = ApprovalView(
                    request_id=request_id,
                    allowed_user_id=guild.owner_id,
                    guild=guild,
                )

                await interaction.followup.send(
                    embed=embed,
                    view=view,
                )

                created += 1

                continue

            # ========================================
            # RENAME CHANNEL
            # ========================================

            if action_type == "rename_channel":

                channel_id = action.get(
                    "channel_id"
                )

                new_name = action.get(
                    "new_name"
                )

                channel = guild.get_channel(
                    channel_id
                )

                if channel is None:
                    continue

                if not isinstance(
                    channel,
                    (
                        discord.TextChannel,
                        discord.VoiceChannel,
                    ),
                ):
                    continue

                if not isinstance(
                    new_name,
                    str,
                ):
                    continue

                new_name = new_name.strip()

                if not new_name:
                    continue

                if len(new_name) > 100:
                    continue

                action_request = ActionRequest(
                    action="rename_channel",
                    target_id=channel.id,
                    target_name=channel.name,
                    reason=request,
                    data={
                        "channel_id": channel.id,
                        "new_name": new_name,
                    },
                )

                decision = evaluate_action(
                    action_request
                )

                if not decision["allowed"] and not decision["requires_approval"]:
                    continue

                if not decision["requires_approval"]:
                    continue

                request_id = str(
                    uuid.uuid4()
                )

                create_approval_request(
                    request_id=request_id,
                    action="rename_channel",
                    target_id=channel.id,
                    target_name=channel.name,
                    reason=request,
                    data={
                        "channel_id": channel.id,
                        "new_name": new_name,
                    },
                )

                embed = discord.Embed(
                    title="AI Organization Request",
                    description=(
                        f"**Action:** `rename_channel`\n"
                        f"**Channel:** {channel.mention}\n"
                        f"**New Name:** `{new_name}`\n"
                        f"**Request:** {request}\n\n"
                        "This change requires server-owner approval."
                    ),
                    color=discord.Color.orange(),
                )

                embed.set_footer(
                    text="AI Server Assistant"
                )

                view = ApprovalView(
                    request_id=request_id,
                    allowed_user_id=guild.owner_id,
                    guild=guild,
                )

                await interaction.followup.send(
                    embed=embed,
                    view=view,
                )

                created += 1

                continue

        if created == 0:

            await interaction.followup.send(
                "No valid organization actions were created."
            )