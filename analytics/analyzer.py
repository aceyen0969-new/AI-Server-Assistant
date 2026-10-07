import json

from analytics.reporter import (
    build_activity_report,
)

from analytics.display import (
    print_activity_report,
)

from analytics.database import (
    get_previous_analysis_report,
    record_analysis_report,
)

from ai.provider_router import (
    ask_with_fallback,
)


def calculate_percentage_change(
    current: int,
    previous: int,
):
    if previous == 0:

        if current == 0:
            return 0.0

        return None

    return round(
        (
            (current - previous)
            / previous
        ) * 100,
        2,
    )


def build_historical_comparison(
    current_report: dict,
    previous_report: dict | None,
):
    if previous_report is None:

        return {
            "available": False,
            "message": "No previous analysis report is available.",
        }

    previous_messages = previous_report.get(
        "total_messages",
        0,
    )

    previous_members = previous_report.get(
        "unique_members",
        0,
    )

    current_messages = current_report.get(
        "total_messages",
        0,
    )

    current_members = current_report.get(
        "unique_members",
        0,
    )

    return {
        "available": True,
        "previous_report_id": previous_report.get(
            "id"
        ),
        "previous_created_at": previous_report.get(
            "created_at"
        ),
        "previous_period_days": previous_report.get(
            "period_days"
        ),
        "previous_total_messages": previous_messages,
        "previous_unique_members": previous_members,
        "current_total_messages": current_messages,
        "current_unique_members": current_members,
        "message_change_percent": calculate_percentage_change(
            current_messages,
            previous_messages,
        ),
        "member_change_percent": calculate_percentage_change(
            current_members,
            previous_members,
        ),
    }


def build_analysis_prompt(
    report: dict,
    historical_comparison: dict,
):
    return f"""
You are an analytics AI for a Discord server.

Analyze the provided server activity data.

Your job is to identify useful, evidence-based patterns and recommend conservative improvements.

The server activity data does not contain message content.

Current report:

{json.dumps(report, indent=2)}

Historical comparison:

{json.dumps(historical_comparison, indent=2)}

Rules:

1. Only make claims supported by the provided data.
2. Do not invent information.
3. Do not infer what users discussed.
4. Do not infer user opinions or emotions.
5. Do not identify users by name.
6. Treat user IDs as anonymous identifiers.
7. Do not recommend structural server changes from extremely small datasets.
8. If total messages are fewer than 10, avoid structural or actionable proposals.
9. If fewer than 3 unique members are active, avoid structural or actionable proposals.
10. When data is insufficient, prefer monitoring and collecting more data.
11. Do not treat a single-day spike as proof of a long-term trend.
12. The daily_trend value was calculated by Python and should be treated as a supporting metric, not absolute proof.
13. A historical comparison is only available when available is true.
14. Do not claim growth or decline when the previous value was zero unless the current data clearly supports describing it as new activity.
15. Percentage changes are calculated by Python and should be treated as supporting evidence.
16. Do not recommend creating, deleting, renaming, or reorganizing channels unless the available evidence strongly supports the recommendation.
17. Supported automatic proposal action:
    - create_channel
18. If there is no strong actionable recommendation, set action to null.
19. Prefer a small number of high-quality observations over many repetitive observations.
20. Keep proposals conservative.
21. Never execute actions.
22. Never output anything outside the required JSON object.

Return exactly this JSON structure:

{{
    "summary": "Short overall summary.",
    "observations": [
        {{
            "title": "Observation title",
            "description": "Evidence-based explanation.",
            "evidence": "Specific data supporting the observation."
        }}
    ],
    "proposals": [
        {{
            "title": "Proposal title",
            "description": "What could be improved.",
            "reason": "Why the data supports this proposal.",
            "action": null
        }}
    ]
}}
"""


def validate_analysis(
    analysis,
):
    if not isinstance(
        analysis,
        dict,
    ):
        return False

    if not isinstance(
        analysis.get("summary"),
        str,
    ):
        return False

    if not isinstance(
        analysis.get("observations"),
        list,
    ):
        return False

    if not isinstance(
        analysis.get("proposals"),
        list,
    ):
        return False

    return True


def print_analysis_result(
    provider_name: str,
    report: dict,
    analysis: dict,
    historical_comparison: dict,
):
    print()
    print("========================================")
    print("         ANALYTICS ANALYSIS")
    print("========================================")

    print()
    print(
        f"Reporting period: {report['period_days']} days"
    )

    print(
        f"AI provider: {provider_name}"
    )

    print()
    print("CURRENT ACTIVITY")
    print(
        f"  Messages: {report['total_messages']}"
    )
    print(
        f"  Active members: {report['unique_members']}"
    )

    metrics = report.get(
        "metrics",
        {},
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
            f"{busiest_channel.get('message_count')}"
        )

    busiest_day = metrics.get(
        "busiest_day"
    )

    if busiest_day:

        print(
            "  Busiest day: "
            f"{busiest_day.get('date')}"
        )

        print(
            "  Day messages: "
            f"{busiest_day.get('message_count')}"
        )

    busiest_hour = metrics.get(
        "busiest_hour"
    )

    if busiest_hour:

        print(
            "  Busiest hour: "
            f"{busiest_hour.get('hour')}:00 UTC"
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

    print(
        "  Activity trend: "
        f"{trend_labels.get(metrics.get('daily_trend', 'unknown'), '❓ Unknown')}"
    )

    print()
    print("HISTORICAL COMPARISON")

    if historical_comparison.get(
        "available"
    ):

        print(
            "  Previous report ID: "
            f"{historical_comparison.get('previous_report_id')}"
        )

        print(
            "  Previous messages: "
            f"{historical_comparison.get('previous_total_messages')}"
        )

        print(
            "  Current messages: "
            f"{historical_comparison.get('current_total_messages')}"
        )

        print(
            "  Message change: "
            f"{historical_comparison.get('message_change_percent')}%"
        )

        print(
            "  Previous members: "
            f"{historical_comparison.get('previous_unique_members')}"
        )

        print(
            "  Current members: "
            f"{historical_comparison.get('current_unique_members')}"
        )

        print(
            "  Member change: "
            f"{historical_comparison.get('member_change_percent')}%"
        )

    else:

        print(
            "  No previous report available."
        )

    print()
    print("AI SUMMARY")
    print(
        f"  {analysis.get('summary', 'No summary provided.')}"
    )

    observations = analysis.get(
        "observations",
        [],
    )

    print()
    print(
        f"OBSERVATIONS ({len(observations)})"
    )

    for index, observation in enumerate(
        observations,
        start=1,
    ):

        if not isinstance(
            observation,
            dict,
        ):
            continue

        title = observation.get(
            "title",
            "Observation",
        )

        description = observation.get(
            "description",
            "",
        )

        evidence = observation.get(
            "evidence",
            "",
        )

        print()
        print(
            f"  {index}. {title}"
        )

        print(
            f"     {description}"
        )

        if evidence:

            print(
                f"     Evidence: {evidence}"
            )

    proposals = analysis.get(
        "proposals",
        [],
    )

    print()
    print(
        f"PROPOSALS ({len(proposals)})"
    )

    for index, proposal in enumerate(
        proposals,
        start=1,
    ):

        if not isinstance(
            proposal,
            dict,
        ):
            continue

        title = proposal.get(
            "title",
            "Proposal",
        )

        description = proposal.get(
            "description",
            "",
        )

        action = proposal.get(
            "action"
        )

        print()
        print(
            f"  {index}. {title}"
        )

        print(
            f"     {description}"
        )

        print(
            f"     Action: {action}"
        )

    print()
    print("========================================")
    print()


async def analyze_server(
    guild_id: int,
    days: int = 7,
):
    report = build_activity_report(
        guild_id,
        days,
    )

    print_activity_report(
        report
    )

    previous_report = get_previous_analysis_report(
        guild_id
    )

    historical_comparison = build_historical_comparison(
        report,
        previous_report,
    )

    prompt = build_analysis_prompt(
        report,
        historical_comparison,
    )

    provider_name, raw_response = (
        await ask_with_fallback(
            prompt
        )
    )

    if raw_response is None:

        print(
            "ANALYTICS: All AI providers failed."
        )

        return {
            "provider": None,
            "report": report,
            "analysis": None,
            "historical_comparison": historical_comparison,
        }

    print(
        f"ANALYTICS: {provider_name} returned a response."
    )

    try:

        analysis = json.loads(
            raw_response
        )

    except json.JSONDecodeError:

        print(
            "ANALYTICS: AI returned invalid JSON."
        )

        print(
            raw_response
        )

        return {
            "provider": provider_name,
            "report": report,
            "analysis": None,
            "historical_comparison": historical_comparison,
        }

    if not validate_analysis(
        analysis
    ):

        print(
            "ANALYTICS: AI analysis failed validation."
        )

        return {
            "provider": provider_name,
            "report": report,
            "analysis": None,
            "historical_comparison": historical_comparison,
        }

    record_analysis_report(
        guild_id=guild_id,
        period_days=days,
        total_messages=report["total_messages"],
        unique_members=report["unique_members"],
        provider=provider_name,
        analysis_json=json.dumps(
            analysis
        ),
    )

    print(
        "ANALYTICS: Analysis report saved."
    )

    print_analysis_result(
        provider_name=provider_name,
        report=report,
        analysis=analysis,
        historical_comparison=historical_comparison,
    )

    return {
        "provider": provider_name,
        "report": report,
        "analysis": analysis,
        "historical_comparison": historical_comparison,
    }