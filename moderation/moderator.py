
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


    async def cleanup_warning(
        self,
        warning_message: discord.Message
    ):

        await asyncio.sleep(10)

        try:

            await warning_message.delete()

            print(
                "🧹 Warning cleanup: SUCCESS"
            )

        except discord.NotFound:

            print(
                "🧹 Warning cleanup: "
                "already deleted."
            )

        except discord.Forbidden:

            print(
                "❌ Warning cleanup: "
                "missing permission."
            )

        except discord.HTTPException as e:

            print(
                "❌ Warning cleanup: "
                "Discord error."
            )

            print(e)

        except Exception as e:

            print(
                "❌ Warning cleanup: "
                "unexpected error."
            )

            print(
                f"Error: {type(e).__name__}: {e}"
            )


    async def handle_message(
        self,
        message: discord.Message
    ):

        if message.author.bot:
            return

        if message.guild is None:
            return

        if not message.content.strip():
            return


        # =============================================
        # SPAM DETECTION
        # =============================================

        result = self.detector.check_message(
            guild_id=message.guild.id,
            user_id=message.author.id,
            content=message.content
        )

        if not result["is_spam"]:
            return


        # =============================================
        # VIOLATION TRACKING
        # =============================================

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
            f"Violation count: "
            f"{violation_count}"
        )


        # =============================================
        # ESCALATION
        # =============================================

        if violation_count == 1:

            escalation = "delete"

        elif violation_count == 2:

            escalation = "warn"

        else:

            escalation = "timeout"


        print(
            f"Escalation: {escalation}"
        )


        # =============================================
        # DELETE SPAM
        # =============================================

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
                "violation_count": (
                    violation_count
                )
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


        # =============================================
        # WARNING
        # =============================================

        if violation_count == 2:

            print(
                "⚠️ Entering warning system..."
            )

            try:

                print(
                    "📨 Attempting to send "
                    "warning message..."
                )

                warning_message = (
                    await message.channel.send(
                        f"⚠️ {message.author.mention}, "
                        f"please stop spamming.\n\n"
                        f"This is your "
                        f"**2nd moderation violation**.\n"
                        f"**Reason:** "
                        f"{result['reason']}"
                    )
                )


                print(
                    "✅ Warning: SUCCESS"
                )

                print(
                    f"Warning message ID: "
                    f"{warning_message.id}"
                )


                asyncio.create_task(
                    self.cleanup_warning(
                        warning_message
                    )
                )


                print(
                    "🧹 Warning cleanup scheduled."
                )


            except discord.Forbidden as e:

                print(
                    "❌ Warning: FORBIDDEN"
                )

                print(
                    f"Error: {e}"
                )


            except discord.HTTPException as e:

                print(
                    "❌ Warning: "
                    "DISCORD HTTP ERROR"
                )

                print(
                    f"Error: {e}"
                )


            except Exception as e:

                print(
                    "❌ Warning: "
                    "UNEXPECTED ERROR"
                )

                print(
                    f"Error type: "
                    f"{type(e).__name__}"
                )

                print(
                    f"Error: {e}"
                )


        # =============================================
        # TIMEOUT
        # =============================================

        if violation_count >= 3:

            timeout_request = ActionRequest(
                action="timeout_member",
                target_id=message.author.id,
                target_name=message.author.name,
                reason=(
                    "Repeated spam violations. "
                    f"Violation #{violation_count}."
                ),
                data={
                    "guild_id": message.guild.id,
                    "channel_id": (
                        message.channel.id
                    ),
                    "duration_seconds": 60,
                    "violation_count": (
                        violation_count
                    )
                }
            )


            if can_execute_automatically(
                timeout_request
            ):

                timeout_result = (
                    await execute_action(
                        timeout_request,
                        member=message.author
                    )
                )


                if timeout_result["success"]:

                    print(
                        "⏱️ Timeout: SUCCESS"
                    )

                    print(
                        "Duration: "
                        f"{timeout_result['duration_seconds']} "
                        "seconds"
                    )

                else:

                    print(
                        "❌ Timeout: FAILED"
                    )

                    print(
                        f"Reason: "
                        f"{timeout_result['error']}"
                    )

            else:

                print(
                    "❌ Timeout: "
                    "BLOCKED BY SECURITY POLICY"
                )


        print("----------------------------------------")


moderation_manager = ModerationManager()