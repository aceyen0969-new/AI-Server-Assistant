import time
from collections import defaultdict, deque


class SpamDetector:
    def __init__(
        self,
        max_messages=5,
        time_window=5,
        duplicate_limit=3
    ):
        self.max_messages = max_messages
        self.time_window = time_window
        self.duplicate_limit = duplicate_limit

        self.message_history = defaultdict(
            lambda: deque()
        )

        self.duplicate_history = defaultdict(
            lambda: deque()
        )

    def check_message(
        self,
        guild_id,
        user_id,
        content
    ):
        now = time.time()

        key = (
            guild_id,
            user_id
        )

        history = self.message_history[key]

        while history and now - history[0] > self.time_window:
            history.popleft()

        history.append(now)

        if len(history) >= self.max_messages:
            return {
                "is_spam": True,
                "type": "message_flood",
                "reason": (
                    f"User sent {len(history)} messages "
                    f"within {self.time_window} seconds."
                )
            }

        duplicate_history = self.duplicate_history[key]

        while (
            duplicate_history
            and now - duplicate_history[0][0] > self.time_window
        ):
            duplicate_history.popleft()

        duplicate_history.append(
            (now, content)
        )

        duplicate_count = sum(
            1
            for _, previous_content in duplicate_history
            if previous_content == content
        )

        if duplicate_count >= self.duplicate_limit:
            return {
                "is_spam": True,
                "type": "duplicate_message",
                "reason": (
                    f"User sent the same message "
                    f"{duplicate_count} times within "
                    f"{self.time_window} seconds."
                )
            }

        return {
            "is_spam": False,
            "type": None,
            "reason": None
        }

    def reset_user(
        self,
        guild_id,
        user_id
    ):
        key = (
            guild_id,
            user_id
        )

        self.message_history.pop(
            key,
            None
        )

        self.duplicate_history.pop(
            key,
            None
        )