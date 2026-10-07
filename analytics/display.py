import discord


def print_activity_report(
    report: dict,
    guild: discord.Guild | None = None,
):
    metrics = report.get(
        "metrics",
        {},
    )

    print()
    print("========================================")
    print("          QUASAR ANALYTICS")
    print("========================================")

    print()
    print("REPORTING PERIOD")
    print(
        f"  Last {report.get('period_days', '?')} days"
    )

    print()
    print("ACTIVITY")
    print(
        f"  Messages: {report.get('total_messages', 0)}"
    )
    print(
        f"  Active members: {report.get('unique_members', 0)}"
    )
    print(
        "  Avg. messages / member: "
        f"{metrics.get('average_messages_per_member', 0)}"
    )

    print()
    print("PEAK ACTIVITY")

    busiest_channel = metrics.get(
        "busiest_channel"
    )

    if busiest_channel:

        channel_id = busiest_channel.get(
            "channel_id"
        )

        channel_name = f"#{channel_id}"

        if guild is not None:

            channel = guild.get_channel(
                channel_id
            )

            if channel is not None:

                channel_name = f"#{channel.name}"

        print(
            "  Busiest channel: "
            f"{channel_name}"
        )

        print(
            "  Channel messages: "
            f"{busiest_channel.get('message_count', 0)}"
        )

    busiest_day = metrics.get(
        "busiest_day"
    )

    if busiest_day:

        print(
            "  Busiest day: "
            f"{busiest_day.get('date', 'Unknown')}"
        )

        print(
            "  Day messages: "
            f"{busiest_day.get('message_count', 0)}"
        )

    busiest_hour = metrics.get(
        "busiest_hour"
    )

    if busiest_hour:

        print(
            "  Busiest hour: "
            f"{busiest_hour.get('hour', '?')}:00 UTC"
        )

    trend_labels = {
        "increasing": "Increasing",
        "decreasing": "Decreasing",
        "stable": "Stable",
        "sporadic": "Sporadic",
        "insufficient_data": "Insufficient data",
        "no_activity": "No activity",
        "unknown": "Unknown",
    }

    daily_trend = metrics.get(
        "daily_trend",
        "unknown",
    )

    print(
        "  Activity trend: "
        f"{trend_labels.get(daily_trend, 'Unknown')}"
    )

    print()
    print("========================================")
    print()