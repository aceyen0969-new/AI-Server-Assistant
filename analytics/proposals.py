import uuid

import discord

from security.actions import (
    ActionRequest,
    evaluate_action,
)

from security.approval import create_approval_request
from security.approval_view import ApprovalView


async def process_analytics_proposals(
    guild: discord.Guild,
    proposals: list,
    send_function,
):
    """Process AI-generated analytics proposals."""

    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue

        action = proposal.get("action")

        # Informational proposals do not need approval.
        if action is None:
            continue

        if not isinstance(action, dict):
            continue

        action_type = action.get("action")

        if action_type != "create_channel":
            print(
                "ANALYTICS: Ignoring unsupported "
                f"proposal action: {action_type}"
            )
            continue

        name = action.get("name")
        channel_type = action.get("channel_type")

        if not isinstance(name, str):
            continue

        name = name.strip()

        if not name or len(name) > 100:
            continue

        if channel_type not in ("text", "voice"):
            continue

        existing_channel = discord.utils.get(
            guild.channels,
            name=name,
        )

        if existing_channel is not None:
            print(
                "ANALYTICS: Skipping create_channel proposal "
                f"because #{name} already exists."
            )
            continue

        title = proposal.get("title", "Create Channel")
        description = proposal.get("description", "")
        reason = proposal.get("reason", description)

        if not isinstance(reason, str):
            reason = str(reason)

        action_request = ActionRequest(
            action="create_channel",
            target_name=name,
            reason=reason,
            data={
                "name": name,
                "channel_type": channel_type,
            },
        )

        decision = evaluate_action(action_request)

        if not decision["allowed"] or not decision["requires_approval"]:
            print(
                "ANALYTICS: Security rejected or did not require "
                "approval for create_channel. Skipping proposal."
            )
            continue

        request_id = str(uuid.uuid4())

        create_approval_request(
            request_id=request_id,
            action="create_channel",
            target_name=name,
            reason=reason,
            data={
                "name": name,
                "channel_type": channel_type,
            },
            guild_id=guild.id,
            approver_id=guild.owner_id,
        )

        proposal_embed = discord.Embed(
            title="💡 AI Server Improvement Proposal",
            description=(
                f"**Proposal:** {title}\n\n"
                f"{description}\n\n"
                f"**Reason:** {reason}\n\n"
                f"**Action:** `create_channel`\n"
                f"**Name:** `{name}`\n"
                f"**Type:** `{channel_type}`\n\n"
                "This change requires server-owner approval."
            ),
            color=discord.Color.orange(),
        )

        proposal_embed.set_footer(
            text="AI Server Assistant"
        )

        view = ApprovalView(
            request_id=request_id,
            allowed_user_id=guild.owner_id,
            guild=guild,
        )

        await send_function(
            embed=proposal_embed,
            view=view,
        )

        print(
            "ANALYTICS: Approval request sent "
            f"for create_channel #{name}."
        )