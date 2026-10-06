import time
from collections import defaultdict

VIOLATION_DECAY_SECONDS = 10 * 60

class ViolationTracker:

    def __init__(self):
        self.violations = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "count": 0,
                    "last_violation": 0.0
                }
            )
        )

    def _apply_decay(self, guild_id: int, user_id: int):
        record = self.violations[guild_id][user_id]

        count = record["count"]
        last_violation = record["last_violation"]

        if count <= 0 or last_violation <= 0:
            return

        elapsed = time.time() - last_violation

        decay_amount = int(
            elapsed // VIOLATION_DECAY_SECONDS
        )

        if decay_amount <= 0:
            return

        new_count = max(
            0,
            count - decay_amount
        )

        record["count"] = new_count

        if new_count == 0:
            self.violations[guild_id].pop(
                user_id,
                None
            )
            return

        record["last_violation"] += (
            decay_amount
            * VIOLATION_DECAY_SECONDS
        )

    def add_violation(
        self,
        guild_id: int,
        user_id: int
    ) -> int:

        self._apply_decay(
            guild_id,
            user_id
        )

        record = self.violations[guild_id][user_id]

        record["count"] += 1
        record["last_violation"] = time.time()

        return record["count"]

    def get_violations(
        self,
        guild_id: int,
        user_id: int
    ) -> int:

        self._apply_decay(
            guild_id,
            user_id
        )

        if user_id not in self.violations[guild_id]:
            return 0

        return self.violations[guild_id][user_id]["count"]

    def reset_user(
        self,
        guild_id: int,
        user_id: int
    ):

        if guild_id in self.violations:
            self.violations[guild_id].pop(
                user_id,
                None
            )

    def reset_guild(
        self,
        guild_id: int
    ):

        self.violations.pop(
            guild_id,
            None
        )

violation_tracker = ViolationTracker()
