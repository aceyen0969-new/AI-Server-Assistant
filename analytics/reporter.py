from analytics.database import (
    get_message_count,
    get_unique_member_count,
    get_channel_activity,
    get_member_activity,
    get_hourly_activity,
)


def build_activity_report(
    guild_id: int,
):
    """Build a complete activity report for a Discord server."""

    total_messages = get_message_count(
        guild_id
    )

    unique_members = get_unique_member_count(
        guild_id
    )

    channels = get_channel_activity(
        guild_id
    )

    members = get_member_activity(
        guild_id
    )

    hourly_activity = get_hourly_activity(
        guild_id
    )

    return {
        "guild_id": guild_id,
        "total_messages": total_messages,
        "unique_members": unique_members,
        "channels": channels,
        "members": members,
        "hourly_activity": hourly_activity,
    }