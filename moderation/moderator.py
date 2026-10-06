import discord

from moderation.detector import SpamDetector
from security.actions import (
    ActionRequest,
    can_execute_automatically
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
        # Ignore bots.
        if message.author.bot:
            return

        # Ignore DMs.
        if message.guild is None:
            return

        # Ignore empty messages.
        if not message.content.strip():
            return

        result = self.detector.check_message(
            guild_id=message.guild.id,
            user_id=message.author.id,
            content=message.content
        )

        if not result["is_spam"]:
            return

        action_request = ActionRequest(
            action="delete_spam",
            target_id=message.id,
            target_name=message.author.name,
            reason=result["reason"],
            data={
                "guild_id": message.guild.id,
                "channel_id": message.channel.id,
                "message_id": message.id,
                "spam_type": result["type"]
            }
        )

        if not can_execute_automatically(
            action_request
        ):
            print(
                "⚠️ Spam detected, but the action "
                "was not allowed automatically."
            )
            return

        try:
            await message.delete()

            print("----------------------------------------")
            print("🛡️ AI Moderation")
            print(f"User: {message.author}")
            print(f"Action: delete_spam")
            print(f"Type: {result['type']}")
            print(f"Reason: {result['reason']}")
            print("Result: SUCCESS")
            print("----------------------------------------")

        except discord.NotFound:
            print(
                "⚠️ Spam message was already deleted."
            )

        except discord.Forbidden:
            print(
                "❌ Quasar does not have permission "
                "to delete this message."
            )

        except discord.HTTPException as e:
            print(
                "❌ Discord rejected the message deletion."
            )
            print(e)


moderation_manager = ModerationManager()
