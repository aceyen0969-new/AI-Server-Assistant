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
2. Which channels are most or least active.
3. Member participation.
4. Activity patterns by hour.
5. Potential organizational improvements.
6. Potential issues that the server owner may want to investigate.

IMPORTANT:

- Do not assume why a member behaves a certain way.
- Do not make personal judgments about members.
- Do not recommend actions based solely on one member.
- Do not expose message contents because message contents
  are not provided.
- Clearly distinguish observations from recommendations.
- Recommendations are suggestions only.
- Never perform an action yourself.
- Remember that a small amount of data may not be enough
  to make a strong conclusion.
- Avoid presenting temporary activity as a long-term trend.
- State when more data is needed.

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
            "reason": "Why the data supports this proposal."
        }}
    ]
}}

If there are not enough data points to make a useful
observation or proposal, return an empty list instead.

Example:

{{
    "summary": "The server has moderate activity concentrated in a small number of channels.",
    "observations": [
        {{
            "title": "Activity is concentrated",
            "description": "Most recorded messages come from one channel.",
            "evidence": "The channel accounts for most recorded messages."
        }}
    ],
    "proposals": []
}}
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