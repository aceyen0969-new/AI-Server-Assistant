from dataclasses import dataclass, field
from typing import Any

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
    message: Any = None
):

    """
    Execute automatic moderation actions.

    Security policy decides whether an action is allowed.
    This function performs the actual Discord action.
    """

    if not can_execute_automatically(
        request
    ):
        return {
            "success": False,
            "error": (
                "Action is not allowed "
                "automatically."
            )
        }


    # =====================================================
    # DELETE SPAM
    # =====================================================

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


        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }


    return {
        "success": False,
        "error": (
            f"No executor exists for "
            f"'{request.action}'."
        )
    }

import asyncio

import discord

from moderation.detector import SpamDetector
from moderation.violations import violation_tracker

from security.actions import (
    ActionRequest,
    can_execute_automatically,
    execute_action
)


class ModerationManager:

    def __init__(self):

        self.detector = SpamDetector(
            max_messages=5,
            time_window=5,
            duplicate_limit=3
        )


    async def handle_message(
        self,
        message: discord.Message
    ):

        # -------------------------------------------------
        # IGNORE BOTS
        # -------------------------------------------------

        if message.author.bot:
            return


        # -------------------------------------------------
        # IGNORE DMS
        # -------------------------------------------------

        if message.guild is None:
            return


        # -------------------------------------------------
        # IGNORE EMPTY MESSAGES
        # -------------------------------------------------

        if not message.content.strip():
            return


        # -------------------------------------------------
        # CHECK FOR SPAM
        # -------------------------------------------------

        result = self.detector.check_message(
            guild_id=message.guild.id,
            user_id=message.author.id,
            content=message.content
        )


        if not result["is_spam"]:
            return


        # -------------------------------------------------
        # RECORD VIOLATION
        # -------------------------------------------------

        violation_count = (
            violation_tracker.add_violation(
                guild_id=message.guild.id,
                user_id=message.author.id
            )
        )


        print("----------------------------------------")
        print("🛡️ AI Moderation")
        print(f"User: {message.author}")
        print(f"Type: {result['type']}")
        print(f"Reason: {result['reason']}")
        print(
            f"Violation count: {violation_count}"
        )


        # -------------------------------------------------
        # DETERMINE ESCALATION
        # -------------------------------------------------

        if violation_count == 1:

            escalation = "delete"

        elif violation_count == 2:

            escalation = "warn"

        else:

            escalation = "timeout"


        print(
            f"Escalation: {escalation}"
        )


        # =================================================
        # DELETE SPAM
        # =================================================

        delete_request = ActionRequest(
            action="delete_spam",
            target_id=message.id,
            target_name=message.author.name,
            reason=result["reason"],
            data={
                "guild_id": message.guild.id,
                "channel_id": message.channel.id,
                "message_id": message.id,
                "spam_type": result["type"],
                "violation_count": violation_count
            }
        )


        if can_execute_automatically(
            delete_request
        ):

            delete_result = await execute_action(
                delete_request,
                message=message
            )


            if delete_result["success"]:

                print(
                    "Delete: SUCCESS"
                )

            else:

                print(
                    "Delete: FAILED"
                )

                print(
                    f"Reason: "
                    f"{delete_result['error']}"
                )


        # =================================================
        # PUBLIC WARNING
        # =================================================

        if violation_count == 2:

            try:

                warning_message = await message.channel.send(
                    f"⚠️ {message.author.mention}, "
                    f"please stop spamming.\n\n"
                    f"This is your **2nd moderation "
                    f"violation**.\n"
                    f"**Reason:** {result['reason']}"
                )


                print(
                    "Warning: SUCCESS"
                )


                # -----------------------------------------
                # DELETE WARNING AFTER 10 SECONDS
                # -----------------------------------------

                await asyncio.sleep(10)

                try:

                    await warning_message.delete()

                    print(
                        "Warning cleanup: SUCCESS"
                    )

                except discord.NotFound:

                    print(
                        "Warning cleanup: "
                        "message already deleted."
                    )

                except discord.HTTPException as e:

                    print(
                        "Warning cleanup: FAILED"
                    )

                    print(e)


            except discord.Forbidden:

                print(
                    "Warning: FAILED"
                )

                print(
                    "Reason: Quasar does not have "
                    "permission to send messages."
                )


            except discord.HTTPException as e:

                print(
                    "Warning: FAILED"
                )

                print(e)


        # =================================================
        # TIMEOUT
        # =================================================

        if violation_count >= 3:

            print(
                "Timeout: NOT IMPLEMENTED"
            )

            print(
                "Timeout decision recorded, "
                "but no timeout executor exists yet."
            )


        print("----------------------------------------")


moderation_manager = ModerationManager()