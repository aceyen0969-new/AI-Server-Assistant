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
objective metrics from the activity data.

Use these metrics as factual evidence:

- average_messages_per_member
- busiest_channel
- busiest_hour
- busiest_day
- daily_trend

Do not recalculate these values yourself unless necessary
to explain them.

DAILY ACTIVITY ANALYSIS:

The daily_activity field contains one entry for every day
in the reporting period, including days with zero messages.

Use the complete daily_activity timeline together with
the daily_trend metric.

The Python system calculates daily_trend by dividing the
reporting period into an earlier period and a more recent
period and comparing their total message activity.

Interpret the trend as follows:

- "insufficient_data" means there are not enough daily
  data points to make a meaningful comparison.
- "no_activity" means there was no recorded activity
  during the reporting period.
- "increasing" means the recent period had substantially
  more activity than the earlier period.
- "decreasing" means the recent period had substantially
  less activity than the earlier period.
- "stable" means the activity difference between the
  earlier and recent periods was relatively small.

The current trend thresholds are:

- increasing: recent activity is at least 25% higher
  than earlier activity.
- decreasing: recent activity is at least 25% lower
  than earlier activity.
- stable: the difference is less than 25%.

Do not claim that a trend is a long-term server-wide
pattern unless the reporting period contains enough
historical data to support that conclusion.

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
- Zero-activity days are meaningful evidence and should
  not be ignored.

DATA SUFFICIENCY AND ACTION SAFETY:

Be conservative when the dataset is small.

Do not generate structural or actionable proposals when
the reporting period contains fewer than 10 total messages.

Do not generate structural or actionable proposals when
fewer than 3 unique members are active.

When either threshold is not met, prefer a monitoring or
data-collection proposal with:

"action": null

Do not recommend creating, deleting, renaming, or
reorganizing channels based on very limited activity.

Actionable proposals should require enough evidence that
the proposed Discord change is reasonably justified.

For example, if the report contains only 4 messages from
1 member, do not recommend creating new channels merely
because the existing activity occurred in one channel.

Instead, recommend continued monitoring or collecting
more activity data.

ACTIONABLE PROPOSALS:

Some proposals may be executable by the Discord bot.

Only create an action object when the proposal describes
a specific Discord change that the bot could perform AND
the available activity data provides enough evidence to
justify that change.

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
    "reason": "The activity data provides enough evidence that a dedicated gaming channel would be useful.",
    "action": {{
        "action": "create_channel",
        "name": "gaming",
        "channel_type": "text"
    }}
}}

For a non-actionable proposal:

{{
    "title": "Collect more activity data",
    "description": "Continue monitoring activity over a longer period before drawing strong conclusions.",
    "reason": "There is not enough activity data to justify a structural server change.",
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