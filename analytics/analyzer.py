import json

from analytics.reporter import build_activity_report
from ai.provider_router import ask_with_fallback


def build_analysis_prompt(
    report: dict,
) -> str:
    """Build the prompt used by the AI server analyst."""

    report_json = json.dumps(
        report,
        indent=2,
    )

    period_days = report.get(
        "period_days",
        7,
    )

    return f"""
You are the analytics analyst for a Discord server management assistant.

Your job is to analyze server activity data and identify
useful observations and possible improvements.

You are NOT allowed to perform Discord actions.

You are NOT allowed to invent activity data.

Only make conclusions supported by the provided report.

REPORTING PERIOD:
The following data covers the last {period_days} days.

SERVER ACTIVITY REPORT:
{report_json}

Analyze:

1. Overall server activity.
2. Daily activity trends.
3. Which days are busiest and quietest.
4. Which channels are most or least active.
5. Member participation.
6. Activity patterns by hour.
7. Calculated server metrics.
8. Potential organizational improvements.
9. Potential issues that the server owner may want to investigate.

CALCULATED METRICS:

The Python analytics system has already calculated
objective metrics from the raw activity data.

Use these metrics as factual evidence:

- average_messages_per_member
- busiest_channel
- busiest_hour
- busiest_day
- daily_trend

Do not recalculate these values yourself unless necessary
to explain them.

DAILY ACTIVITY ANALYSIS:

Use the daily_activity data together with the
daily_trend metric.

Interpret the trend carefully:

- "insufficient_data" means there is not enough data
  to determine a meaningful trend.
- "increasing" means the available daily data shows
  activity increasing from the earliest recorded day
  to the latest recorded day.
- "decreasing" means the available daily data shows
  activity decreasing from the earliest recorded day
  to the latest recorded day.
- "stable" means the earliest and latest recorded
  activity levels are equal.

Do not claim that a trend is a long-term server-wide
pattern unless the reporting period contains enough
activity data to support that conclusion.

IMPORTANT:

- Do not assume why a member behaves a certain way.
- Do not make personal judgments about members.
- Do not recommend actions based solely on one member.
- Do not expose message contents because message contents
  are not provided.
- Clearly distinguish observations from recommendations.
- Recommendations are suggestions only.
- Never perform an action yourself.
- A small amount of data may not be enough to make a
  strong conclusion.
- Avoid presenting temporary activity as a long-term trend.
- State when more data is needed.
- Do not invent dates, message counts, users, channels,
  or activity patterns.
- Use the exact evidence provided in the report.

ACTIONABLE PROPOSALS:

Some proposals may be executable by the Discord bot.

Only create an action object when the proposal describes
a specific Discord change that the bot could perform.

Currently supported proposal actions are:

1. create_channel

For create_channel, use this structure:

{{
    "action": "create_channel",
    "name": "channel-name",
    "channel_type": "text"
}}

The channel_type must be either "text" or "voice".

If a proposal is only advice, monitoring, engagement strategy,
or something that the bot cannot directly execute, set:

"action": null

Do NOT invent channel names based on activity data unless
the proposal clearly supports the suggested name.

Do NOT create actions for proposals that are not supported
by the available action types.

Return ONLY valid JSON using this structure:

{{
    "summary": "Short summary of the server's activity.",
    "observations": [
        {{
            "title": "Observation title",
            "description": "What the data shows.",
            "evidence": "Specific evidence from the report."
        }}
    ],
    "proposals": [
        {{
            "title": "Proposal title",
            "description": "What the server owner could consider doing.",
            "reason": "Why the data supports this proposal.",
            "action": null
        }}
    ]
}}

For an actionable proposal:

{{
    "title": "Create a gaming channel",
    "description": "Create a dedicated channel for gaming discussions.",
    "reason": "The server would benefit from a dedicated space for this activity.",
    "action": {{
        "action": "create_channel",
        "name": "gaming",
        "channel_type": "text"
    }}
}}

For a non-actionable proposal:

{{
    "title": "Collect more activity data",
    "description": "Continue monitoring activity before drawing conclusions.",
    "reason": "There is not enough data to establish a reliable trend.",
    "action": null
}}

If there are not enough data points to make a useful
observation or proposal, return an empty list instead.
"""


async def analyze_server(
    guild_id: int,
    days: int = 7,
):
    """Analyze server activity using the AI provider system."""

    report = build_activity_report(
        guild_id,
        days,
    )

    prompt = build_analysis_prompt(
        report
    )

    print(
        "========== ANALYTICS ANALYSIS =========="
    )

    print(
        f"Reporting period: {days} day(s)"
    )

    provider_name, result = await ask_with_fallback(
        prompt
    )

    if result is None:

        print(
            "ANALYTICS: All AI providers failed."
        )

        return {
            "provider": None,
            "report": report,
            "analysis": None,
        }

    print(
        f"ANALYTICS: {provider_name} returned a response."
    )

    try:

        analysis = json.loads(
            result
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ) as e:

        print(
            "ANALYTICS JSON ERROR:"
        )

        print(
            repr(e)
        )

        print(
            "RAW RESPONSE:"
        )

        print(
            result
        )

        return {
            "provider": provider_name,
            "report": report,
            "analysis": None,
        }

    if not isinstance(
        analysis,
        dict,
    ):

        print(
            "ANALYTICS ERROR: "
            "AI response was not a JSON object."
        )

        return {
            "provider": provider_name,
            "report": report,
            "analysis": None,
        }

    return {
        "provider": provider_name,
        "report": report,
        "analysis": analysis,
    }