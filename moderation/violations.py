from collections import defaultdict


class ViolationTracker:
    def __init__(self):
        # Stores violations separately for each server and user.
        #
        # Structure:
        # {
        #     guild_id: {
        #         user_id: violation_count
        #     }
        # }
        self.violations = defaultdict(
            lambda: defaultdict(int)
        )

    def add_violation(self, guild_id, user_id):
        """Add one violation to a user."""

        self.violations[guild_id][user_id] += 1

        return self.violations[guild_id][user_id]

    def get_violations(self, guild_id, user_id):
        """Return the user's current violation count."""

        return self.violations[guild_id][user_id]

    def reset_user(self, guild_id, user_id):
        """Reset a user's violations."""

        if guild_id in self.violations:
            self.violations[guild_id].pop(
                user_id,
                None
            )

    def reset_guild(self, guild_id):
        """Reset all violations in a server."""

        self.violations.pop(
            guild_id,
            None
        )


violation_tracker = ViolationTracker()