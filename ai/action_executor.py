import discord

from security.approval import (
    claim_approved_request,
    complete_approval_request,
    get_approval_request,
    is_expired,
)

from security.policies import get_safety_decision


def _is_valid_approval(
    action: dict,
    reason: str | None,
    approval_request_id: str | None,
) -> bool:
    """Check the approval, policy, and action payload."""

    if not isinstance(approval_request_id, str):
        return False

    if not approval_request_id.strip():
        return False

    request = get_approval_request(approval_request_id)

    if request is None:
        return False

    if request.cancelled or not request.approved:
        return False

    if request.executing or request.completed:
        return False

    if is_expired(approval_request_id):
        return False

    if not isinstance(action, dict):
        return False

    action_type = action.get("action")
    decision = get_safety_decision(action_type)

    if (
        not decision.get("allowed")
        or not decision.get("requires_approval")
        or decision.get("policy") != "approval"
    ):
        return False

    snapshot = request.approved_snapshot

    if not isinstance(snapshot, dict):
        return False

    action_data = {
        key: value
        for key, value in action.items()
        if key != "action"
    }

    if action_type != snapshot.get("action"):
        return False

    if action_data != snapshot.get("data"):
        return False

    if request.action != snapshot.get("action"):
        return False

    if request.data != snapshot.get("data"):
        return False

    if request.reason != snapshot.get("reason"):
        return False

    if reason != snapshot.get("reason"):
        return False

    return True


async def _execute_action_impl(
    guild: discord.Guild,
    action: dict,
    reason: str | None,
) -> bool:
    """Perform the Discord operation after approval is claimed."""

    action_type = action.get("action")

    if action_type == "move_channel":
        channel_id = action.get("channel_id")
        category_id = action.get("category_id")

        if type(channel_id) is not int or type(category_id) is not int:
            return False

        channel = guild.get_channel(channel_id)
        category = guild.get_channel(category_id)

        if channel is None or category is None:
            return False

        if not isinstance(category, discord.CategoryChannel):
            return False

        if not isinstance(
            channel,
            (
                discord.TextChannel,
                discord.VoiceChannel,
                discord.StageChannel,
                discord.ForumChannel,
            ),
        ):
            return False

        try:
            await channel.edit(category=category, reason=reason)
            return True
        except discord.HTTPException as error:
            print(f"ACTION EXECUTOR: Move failed: {error!r}")
            return False

    if action_type == "rename_channel":
        channel_id = action.get("channel_id")
        new_name = action.get("new_name")

        if type(channel_id) is not int:
            return False

        if not isinstance(new_name, str):
            return False

        new_name = new_name.strip()

        if not new_name or len(new_name) > 100:
            return False

        channel = guild.get_channel(channel_id)

        if channel is None:
            return False

        if not isinstance(
            channel,
            (
                discord.TextChannel,
                discord.VoiceChannel,
                discord.StageChannel,
                discord.ForumChannel,
            ),
        ):
            return False

        try:
            await channel.edit(name=new_name, reason=reason)
            return True
        except discord.HTTPException as error:
            print(f"ACTION EXECUTOR: Rename failed: {error!r}")
            return False

    if action_type == "create_channel":
        name = action.get("name")
        channel_type = action.get("channel_type")

        if not isinstance(name, str):
            return False

        name = name.strip()

        if not name or len(name) > 100:
            return False

        if channel_type not in ("text", "voice"):
            return False

        if discord.utils.get(guild.channels, name=name) is not None:
            return False

        try:
            if channel_type == "text":
                await guild.create_text_channel(
                    name=name,
                    reason=reason,
                )
            else:
                await guild.create_voice_channel(
                    name=name,
                    reason=reason,
                )

            return True
        except discord.HTTPException as error:
            print(f"ACTION EXECUTOR: Create failed: {error!r}")
            return False

    return False


async def execute_action(
    guild: discord.Guild,
    action: dict,
    reason: str | None = None,
    approval_request_id: str | None = None,
) -> bool:
    """Execute an organization action through a single-use approval."""

    if not _is_valid_approval(
        action=action,
        reason=reason,
        approval_request_id=approval_request_id,
    ):
        print("ACTION EXECUTOR: Blocked invalid approval.")
        return False

    # This state transition happens before the first await.
    claimed = claim_approved_request(
        request_id=approval_request_id,
        action=action,
        reason=reason,
    )

    if not claimed:
        print("ACTION EXECUTOR: Request could not be claimed.")
        return False

    try:
        success = await _execute_action_impl(
            guild=guild,
            action=action,
            reason=reason,
        )
    except Exception as error:
        print(f"ACTION EXECUTOR: Unexpected failure: {error!r}")
        success = False
    finally:
        # Record the outcome even when the operation fails.
        complete_approval_request(
            request_id=approval_request_id,
            success=locals().get("success", False),
        )

    return success