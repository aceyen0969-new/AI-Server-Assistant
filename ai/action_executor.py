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
    """Validate approval and log the exact reason for rejection."""

    def reject(message: str) -> bool:
        print(f"APPROVAL DEBUG: {message}")
        return False

    if not isinstance(approval_request_id, str):
        return reject("Invalid request ID type.")

    if not approval_request_id.strip():
        return reject("Empty request ID.")

    request = get_approval_request(approval_request_id)

    if request is None:
        return reject("Approval request not found.")

    if request.cancelled:
        return reject("Request has been cancelled.")

    if not request.approved:
        return reject("Request has not been approved.")

    if request.executing:
        return reject("Request is already executing.")

    if request.completed:
        return reject(
            f"Request has already been used. Status: {request.status}"
        )

    if is_expired(approval_request_id):
        return reject("Approval request expired.")

    if not isinstance(action, dict):
        return reject("Action payload is not a dictionary.")

    action_type = action.get("action")
    decision = get_safety_decision(action_type)

    if (
        not decision.get("allowed")
        or not decision.get("requires_approval")
        or decision.get("policy") != "approval"
    ):
        return reject(f"Policy rejected action: {action_type!r}")

    snapshot = request.approved_snapshot

    if not isinstance(snapshot, dict):
        return reject("Approved snapshot is missing.")

    action_data = {
        key: value
        for key, value in action.items()
        if key != "action"
    }

    if action_type != snapshot.get("action"):
        return reject("Action type differs from approved snapshot.")

    if action_data != snapshot.get("data"):
        return reject("Action payload differs from approved snapshot.")

    if request.action != snapshot.get("action"):
        return reject("Stored action differs from approved snapshot.")

    if request.data != snapshot.get("data"):
        return reject("Stored request data changed after approval.")

    if request.reason != snapshot.get("reason"):
        return reject("Stored reason changed after approval.")

    if reason != snapshot.get("reason"):
        return reject("Execution reason differs from approved reason.")

    print("APPROVAL DEBUG: All validation checks passed.")
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

        if type(channel_id) is not int:
            print("ACTION EXECUTOR: Invalid channel ID.")
            return False

        if type(category_id) is not int:
            print("ACTION EXECUTOR: Invalid category ID.")
            return False

        channel = guild.get_channel(channel_id)
        category = guild.get_channel(category_id)

        if channel is None:
            print("ACTION EXECUTOR: Source channel not found.")
            return False

        if category is None:
            print("ACTION EXECUTOR: Target category not found.")
            return False

        if not isinstance(category, discord.CategoryChannel):
            print("ACTION EXECUTOR: Target is not a category.")
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
            print("ACTION EXECUTOR: Unsupported source channel type.")
            return False

        try:
            await channel.edit(
                category=category,
                reason=reason,
            )
            return True

        except discord.HTTPException as error:
            print(f"ACTION EXECUTOR: Move failed: {error!r}")
            return False

    if action_type == "rename_channel":
        channel_id = action.get("channel_id")
        new_name = action.get("new_name")

        if type(channel_id) is not int:
            print("ACTION EXECUTOR: Invalid channel ID.")
            return False

        if not isinstance(new_name, str):
            print("ACTION EXECUTOR: Invalid channel name.")
            return False

        new_name = new_name.strip()

        if not new_name or len(new_name) > 100:
            print("ACTION EXECUTOR: Channel name length is invalid.")
            return False

        channel = guild.get_channel(channel_id)

        if channel is None:
            print(
                f"ACTION EXECUTOR: Channel {channel_id} was not found "
                "in the current guild cache."
            )
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
            print("ACTION EXECUTOR: Unsupported channel type.")
            return False

        try:
            await channel.edit(
                name=new_name,
                reason=reason,
            )
            return True

        except discord.HTTPException as error:
            print(f"ACTION EXECUTOR: Rename failed: {error!r}")
            return False

    if action_type == "create_channel":
        name = action.get("name")
        channel_type = action.get("channel_type")

        if not isinstance(name, str):
            print("ACTION EXECUTOR: Invalid channel name.")
            return False

        name = name.strip()

        if not name or len(name) > 100:
            print("ACTION EXECUTOR: Channel name length is invalid.")
            return False

        if channel_type not in ("text", "voice"):
            print("ACTION EXECUTOR: Unsupported channel type.")
            return False

        existing_channel = discord.utils.get(
            guild.channels,
            name=name,
        )

        if existing_channel is not None:
            print("ACTION EXECUTOR: A channel with that name exists.")
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

    print(f"ACTION EXECUTOR: Unsupported action: {action_type!r}")
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

    # Claim the request before the first Discord API call.
    # This synchronous state change prevents a second execution.
    claimed = claim_approved_request(
        request_id=approval_request_id,
        action=action,
        reason=reason,
    )

    if not claimed:
        print(
            "ACTION EXECUTOR: Request could not be claimed. "
            "It may have expired, changed, or already been used."
        )
        return False

    success = False

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
        recorded = complete_approval_request(
            request_id=approval_request_id,
            success=success,
        )

        if not recorded:
            print(
                "ACTION EXECUTOR: WARNING: Could not record "
                "the final execution status."
            )

    if success:
        print(
            f"ACTION EXECUTOR: Successfully executed "
            f"{action.get('action')!r}."
        )
    else:
        print(
            f"ACTION EXECUTOR: Execution failed for "
            f"{action.get('action')!r}."
        )

    return success