from analytics.database import (
    get_message_count,
    get_unique_member_count,
    get_channel_activity,
    get_member_activity,
    get_hourly_activity,
)


def build_activity_report(
    guild_id: int,
    days: int = 7,
):
    """Build a server activity report for a time window."""

    total_messages = get_message_count(
        guild_id,
        days,
    )

    unique_members = get_unique_member_count(
        guild_id,
        days,
    )

    channels = get_channel_activity(
        guild_id,
        days,
    )

    members = get_member_activity(
        guild_id,
        days,
    )

    hourly_activity = get_hourly_activity(
        guild_id,
        days,
    )

    return {
        "guild_id": guild_id,
        "period_days": days,
        "total_messages": total_messages,
        "unique_members": unique_members,
        "channels": channels,
        "members": members,
        "hourly_activity": hourly_activity,
    }