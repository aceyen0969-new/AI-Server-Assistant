import uuid

import discord

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


async def process_analytics_proposals(
    guild: discord.Guild,
    proposals: list,
    send_function,
):
    """Process AI-generated analytics proposals."""

    for proposal in proposals:

        if not isinstance(
            proposal,
            dict,
        ):
            continue

        action = proposal.get(
            "action"
        )

        # Informational proposal.
        if action is None:
            continue

        if not isinstance(
            action,
            dict,
        ):
            continue

        action_type = action.get(
            "action"
        )

        # ========================================
        # CREATE CHANNEL
        # ========================================

        if action_type == "create_channel":

            name = action.get(
                "name"
            )

            channel_type = action.get(
                "channel_type"
            )

            # Validate channel name.

            if not isinstance(
                name,
                str,
            ):
                continue

            name = name.strip()

            if not name:
                continue

            if len(name) > 100:
                continue

            # Validate channel type.

            if channel_type not in (
                "text",
                "voice",
            ):
                continue

            # Prevent duplicate channels.

            existing_channel = discord.utils.get(
                guild.channels,
                name=name,
            )

            if existing_channel is not None:

                print(
                    "ANALYTICS: Skipping "
                    f"create_channel proposal because "
                    f"#{name} already exists."
                )

                continue

            title = proposal.get(
                "title",
                "Create Channel",
            )

            description = proposal.get(
                "description",
                "",
            )

            reason = proposal.get(
                "reason",
                description,
            )

            # ====================================
            # SECURITY ACTION REQUEST
            # ====================================

            action_request = ActionRequest(
                action="create_channel",
                target_name=name,
                reason=reason,
                data={
                    "name": name,
                    "channel_type": channel_type,
                },
            )

            decision = evaluate_action(
                action_request
            )

            # Security rejected the action.

            if (
                not decision["allowed"]
                and not decision["requires_approval"]
            ):

                print(
                    "ANALYTICS: Security rejected "
                    "create_channel proposal."
                )

                continue

            # Analytics proposals must never
            # automatically execute.

            if not decision["requires_approval"]:

                print(
                    "ANALYTICS: create_channel does not "
                    "require approval. Skipping automatic "
                    "execution."
                )

                continue

            # ====================================
            # CREATE APPROVAL REQUEST
            # ====================================

            request_id = str(
                uuid.uuid4()
            )

            create_approval_request(
                request_id=request_id,
                action="create_channel",
                target_name=name,
                reason=reason,
                data={
                    "name": name,
                    "channel_type": channel_type,
                },
            )

            # ====================================
            # PROPOSAL EMBED
            # ====================================

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

            # ====================================
            # APPROVAL VIEW
            # ====================================

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

            continue

        # ========================================
        # UNSUPPORTED ACTION
        # ========================================

        print(
            "ANALYTICS: Ignoring unsupported "
            f"proposal action: {action_type}"
        )