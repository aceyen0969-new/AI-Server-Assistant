from analytics.database import (
    get_message_count,
    get_unique_member_count,
    get_channel_activity,
    get_member_activity,
    get_hourly_activity,
    get_daily_activity,
)


def calculate_metrics(
    total_messages: int,
    unique_members: int,
    channels: list,
    hourly_activity: list,
    daily_activity: list,
):
    """Calculate useful summary metrics from activity data."""

    average_messages_per_member = 0

    if unique_members > 0:

        average_messages_per_member = (
            total_messages / unique_members
        )

    busiest_channel = None

    if channels:

        busiest_channel = channels[0]

    busiest_hour = None

    if hourly_activity:

        busiest_hour = max(
            hourly_activity,
            key=lambda item: item["message_count"],
        )

    busiest_day = None

    if daily_activity:

        busiest_day = max(
            daily_activity,
            key=lambda item: item["message_count"],
        )

    if len(daily_activity) < 2:

        daily_trend = "insufficient_data"

    else:

        first_day = daily_activity[0]["message_count"]
        last_day = daily_activity[-1]["message_count"]

        if last_day > first_day:

            daily_trend = "increasing"

        elif last_day < first_day:

            daily_trend = "decreasing"

        else:

            daily_trend = "stable"

    return {
        "average_messages_per_member": round(
            average_messages_per_member,
            2,
        ),
        "busiest_channel": busiest_channel,
        "busiest_hour": busiest_hour,
        "busiest_day": busiest_day,
        "daily_trend": daily_trend,
    }


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

    daily_activity = get_daily_activity(
        guild_id,
        days,
    )

    metrics = calculate_metrics(
        total_messages=total_messages,
        unique_members=unique_members,
        channels=channels,
        hourly_activity=hourly_activity,
        daily_activity=daily_activity,
    )

    return {
        "guild_id": guild_id,
        "period_days": days,
        "total_messages": total_messages,
        "unique_members": unique_members,
        "channels": channels,
        "members": members,
        "hourly_activity": hourly_activity,
        "daily_activity": daily_activity,
        "metrics": metrics,
    }