def print_activity_report(
    report: dict,
):
    metrics = report.get(
        "metrics",
        {},
    )

    print()
    print("========================================")
    print("         SERVER ACTIVITY REPORT")
    print("========================================")
    print()

    print(
        f"Reporting period: {report.get('period_days', '?')} days"
    )

    print()
    print("CURRENT ACTIVITY")

    print(
        f"  Messages: {report.get('total_messages', 0)}"
    )

    print(
        f"  Active members: {report.get('unique_members', 0)}"
    )

    print()
    print("ACTIVITY METRICS")

    print(
        "  Avg. messages / member: "
        f"{metrics.get('average_messages_per_member', 0)}"
    )

    busiest_channel = metrics.get(
        "busiest_channel"
    )

    if busiest_channel:

        print(
            "  Busiest channel: "
            f"{busiest_channel.get('channel_id')}"
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
        "increasing": "📈 Increasing",
        "decreasing": "📉 Decreasing",
        "stable": "➡️ Stable",
        "sporadic": "⚡ Sporadic",
        "insufficient_data": "⚠️ Insufficient data",
        "no_activity": "⚪ No activity",
        "unknown": "❓ Unknown",
    }

    daily_trend = metrics.get(
        "daily_trend",
        "unknown",
    )

    print(
        "  Activity trend: "
        f"{trend_labels.get(daily_trend, '❓ Unknown')}"
    )

    print()
    print("========================================")
    print()