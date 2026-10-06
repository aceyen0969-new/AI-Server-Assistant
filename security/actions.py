from dataclasses import dataclass, field
from typing import Any
from datetime import timedelta

import discord

from security.policies import get_safety_decision


@dataclass
class ActionRequest:
    action: str
    target_id: int | None = None
    target_name: str | None = None
    reason: str = ""
    data: dict[str, Any] = field(default_factory=dict)


def evaluate_action(request):
    decision = get_safety_decision(
        request.action
    )

    return {
        "action": request.action,
        "target_id": request.target_id,
        "target_name": request.target_name,
        "reason": request.reason,
        "data": request.data,
        "policy": decision["policy"],
        "allowed": decision["allowed"],
        "requires_approval": decision[
            "requires_approval"
        ]
    }


def can_execute_automatically(request):
    decision = evaluate_action(request)

    return (
        decision["policy"] == "automatic"
        and decision["allowed"]
        and not decision["requires_approval"]
    )


def can_execute_after_approval(request):
    decision = evaluate_action(request)

    return decision["policy"] in (
        "automatic",
        "approval"
    )


def needs_approval(request):
    decision = evaluate_action(request)

    return decision["requires_approval"]


def is_allowed(request):
    decision = evaluate_action(request)

    return decision["allowed"]


async def execute_action(
    request: ActionRequest,
    message: discord.Message | None = None,
    member: discord.Member | None = None
):
    """
    Execute automatic moderation actions.

    Security policy decides whether an action
    is allowed. This function performs the
    actual Discord action.
    """

    if not can_execute_automatically(request):
        return {
            "success": False,
            "error": (
                "Action is not allowed "
                "automatically."
            )
        }

    # =============================================
    # DELETE SPAM
    # =============================================

    if request.action == "delete_spam":

        if message is None:
            return {
                "success": False,
                "error": (
                    "Message object is required."
                )
            }

        try:
            await message.delete()

            return {
                "success": True,
                "action": "delete_spam"
            }

        except discord.NotFound:
            return {
                "success": False,
                "error": (
                    "Message was already deleted."
                )
            }

        except discord.Forbidden:
            return {
                "success": False,
                "error": (
                    "Quasar does not have permission "
                    "to delete this message."
                )
            }

        except discord.HTTPException as e:
            return {
                "success": False,
                "error": str(e)
            }

    # =============================================
    # TIMEOUT MEMBER
    # =============================================

    if request.action == "timeout_member":

        if member is None:
            return {
                "success": False,
                "error": (
                    "Member object is required."
                )
            }

        # Server owners cannot be timed out.
        if member.guild.owner_id == member.id:
            return {
                "success": False,
                "error": (
                    "The server owner cannot "
                    "be timed out."
                )
            }

        # Get Quasar's member object.
        bot_member = member.guild.me

        if bot_member is None:
            return {
                "success": False,
                "error": (
                    "Could not determine Quasar's "
                    "server member information."
                )
            }

        # Discord role hierarchy check.
        if member.top_role >= bot_member.top_role:
            return {
                "success": False,
                "error": (
                    "Quasar's highest role must be "
                    "higher than the target member's "
                    "highest role."
                )
            }

        timeout_seconds = request.data.get(
            "duration_seconds",
            60
        )

        try:

            duration = (
                discord.utils.utcnow()
                + timedelta(
                    seconds=timeout_seconds
                )
            )

            await member.timeout(
                duration,
                reason=request.reason
            )

            return {
                "success": True,
                "action": "timeout_member",
                "duration_seconds": (
                    timeout_seconds
                )
            }

        except discord.Forbidden:
            return {
                "success": False,
                "error": (
                    "Quasar does not have permission "
                    "to timeout this member. Check "
                    "the Moderate Members permission "
                    "and role hierarchy."
                )
            }

        except discord.HTTPException as e:
            return {
                "success": False,
                "error": str(e)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # =============================================
    # UNKNOWN ACTION
    # =============================================

    return {
        "success": False,
        "error": (
            f"No executor exists for "
            f"'{request.action}'."
        )
    }
