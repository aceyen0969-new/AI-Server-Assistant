
import json

from analytics.reporter import build_activity_report
from analytics.display import print_activity_report
from analytics.intelligence import analyze_server_structure

from analytics.database import (
    get_previous_analysis_report,
    get_memories,
    record_analysis_report,
    save_memory,
    save_objective_assessment,
)

from analytics.objectives import build_objective_context
from ai.provider_router import ask_with_fallback


def calculate_percentage_change(current: int, previous: int):
    if previous == 0:
        return 0.0 if current == 0 else None

    return round(((current - previous) / previous) * 100, 2)


def build_historical_comparison(
    current_report: dict,
    previous_report: dict | None,
):
    if previous_report is None:
        return {
            "available": False,
            "message": "No previous analysis report is available.",
        }

    previous_messages = previous_report.get("total_messages", 0)
    previous_members = previous_report.get("unique_members", 0)
    current_messages = current_report.get("total_messages", 0)
    current_members = current_report.get("unique_members", 0)

    return {
        "available": True,
        "previous_report_id": previous_report.get("id"),
        "previous_created_at": previous_report.get("created_at"),
        "previous_period_days": previous_report.get("period_days"),
        "previous_total_messages": previous_messages,
        "previous_unique_members": previous_members,
        "current_total_messages": current_messages,
        "current_unique_members": current_members,
        "message_change_percent": calculate_percentage_change(
            current_messages, previous_messages
        ),
        "member_change_percent": calculate_percentage_change(
            current_members, previous_members
        ),
    }


def build_memory_context(memories: list):
    memory_items = []

    for memory in memories or []:
        if not isinstance(memory, dict):
            continue

        memory_items.append({
            "memory_type": memory.get("memory_type"),
            "content": memory.get("content"),
            "occurrences": memory.get("occurrences", 1),
            "created_at": memory.get("created_at"),
            "last_seen_at": memory.get("last_seen_at"),
        })

    return {
        "available": bool(memory_items),
        "count": len(memory_items),
        "memories": memory_items,
    }


def build_analysis_prompt(
    report: dict,
    historical_comparison: dict,
    memory_context: dict,
    objective_context: list,
):
    deterministic_structure = report.get(
        "deterministic_structure",
        {},
    )

    return f"""
You are an analytics AI for a Discord server.

Analyze the provided server activity data and deterministic structure findings.
Identify evidence-based patterns, evaluate active objectives, and recommend
conservative improvements.

Current activity report:
{json.dumps(report, indent=2)}

Deterministic server structure findings:
{json.dumps(deterministic_structure, indent=2)}

Historical comparison:
{json.dumps(historical_comparison, indent=2)}

Server memory:
{json.dumps(memory_context, indent=2)}

Active server objectives:
{json.dumps(objective_context, indent=2)}

MEMORY RULES:
1. Memories are historical context, not current evidence.
2. Current report data takes priority over memories.
3. Do not assume an old memory remains true.
4. Do not invent facts absent from the provided data.
5. Do not infer message content, opinions, emotions, or identities.
6. Treat deterministic findings as evidence-based suggestions, not commands.
7. A finding does not prove that a channel is incorrectly organized.
8. Some uncategorized channels, empty categories, and duplicate names may be intentional.

OBJECTIVE RULES:
1. Evaluate every active objective when evidence allows.
2. Use current activity data as the primary evidence.
3. Never claim an objective is at risk without supporting evidence.
4. If evidence is insufficient, use "insufficient_evidence".
5. Do not infer arguments, harassment, threats, opinions, or emotions from metadata.
6. Treat user IDs as anonymous identifiers.
7. Do not recommend punitive action based on analytics metadata.
8. Never execute actions.

GENERAL RULES:
1. Only make claims supported by the provided data.
2. Do not invent information or infer what users discussed.
3. Do not identify users by name.
4. If fewer than 10 messages exist, avoid structural or actionable proposals.
5. If fewer than 3 unique members are active, avoid structural or actionable proposals.
6. Prefer monitoring when evidence is insufficient.
7. Do not treat a one-day spike as proof of a long-term trend.
8. Treat Python-calculated trends and percentage changes as supporting metrics.
9. Do not claim growth from a previous zero value as a percentage.
10. Do not recommend creating, deleting, renaming, or reorganizing channels
    unless the available evidence strongly supports the recommendation.
11. Supported proposal action: create_channel.
12. If no strong actionable recommendation exists, set action to null.
13. Prefer a small number of useful observations over repetitive ones.
14. Never execute actions.
15. Return only the required JSON object.

For objective assessments, return one object for every active objective.

Return exactly this JSON structure:
{{
    "summary": "Short overall summary.",
    "objectives": [
        {{
            "id": 1,
            "objective": "Objective text.",
            "status": "safe|at_risk|insufficient_evidence",
            "assessment": "Evidence-based assessment.",
            "evidence": "Specific supporting data."
        }}
    ],
    "observations": [
        {{
            "title": "Observation title",
            "description": "Evidence-based explanation.",
            "evidence": "Specific supporting data."
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


def validate_analysis(analysis):
    if not isinstance(analysis, dict):
        return False

    if not isinstance(analysis.get("summary"), str):
        return False

    if not isinstance(analysis.get("objectives"), list):
        return False

    if not isinstance(analysis.get("observations"), list):
        return False

    if not isinstance(analysis.get("proposals"), list):
        return False

    valid_statuses = {
        "safe",
        "at_risk",
        "insufficient_evidence",
    }

    for objective in analysis["objectives"]:
        if not isinstance(objective, dict):
            return False

        objective_id = objective.get("id")

        if not isinstance(objective_id, int) or isinstance(
            objective_id, bool
        ):
            return False

        if not isinstance(objective.get("objective"), str):
            return False

        if objective.get("status") not in valid_statuses:
            return False

        if not isinstance(objective.get("assessment"), str):
            return False

        if not isinstance(objective.get("evidence"), str):
            return False

    for observation in analysis["observations"]:
        if not isinstance(observation, dict):
            return False

        if not isinstance(observation.get("title"), str):
            return False

        if not isinstance(observation.get("description"), str):
            return False

        if not isinstance(observation.get("evidence"), str):
            return False

    for proposal in analysis["proposals"]:
        if not isinstance(proposal, dict):
            return False

        for field in ("title", "description", "reason"):
            if not isinstance(proposal.get(field), str):
                return False

        action = proposal.get("action")

        if action is not None and not isinstance(action, dict):
            return False

        if isinstance(action, dict) and action.get("type") != "create_channel":
            return False

    return True


def save_analysis_memories(guild_id: int, analysis: dict):
    saved_count = 0

    for observation in analysis.get("observations", []):
        if not isinstance(observation, dict):
            continue

        title = observation.get("title", "").strip()
        description = observation.get("description", "").strip()
        evidence = observation.get("evidence", "").strip()

        if not title or not description:
            continue

        content = f"{title} {description}"

        if evidence:
            content += f" Evidence: {evidence}"

        save_memory(
            guild_id=guild_id,
            memory_type="observation",
            content=content,
        )
        saved_count += 1

    return saved_count


def save_analysis_objective_assessments(guild_id: int, analysis: dict):
    saved_count = 0

    for objective in analysis.get("objectives", []):
        if not isinstance(objective, dict):
            continue

        objective_id = objective.get("id")
        status = objective.get("status")
        assessment = objective.get("assessment", "")
        evidence = objective.get("evidence", "")

        if not isinstance(objective_id, int) or isinstance(
            objective_id, bool
        ):
            continue

        if status not in {
            "safe",
            "at_risk",
            "insufficient_evidence",
        }:
            continue

        if not isinstance(assessment, str) or not isinstance(evidence, str):
            continue

        save_objective_assessment(
            objective_id=objective_id,
            guild_id=guild_id,
            status=status,
            assessment=assessment,
            evidence=evidence,
        )
        saved_count += 1

    return saved_count


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
    print(f"Reporting period: {report.get('period_days', '?')} days")
    print(f"AI provider: {provider_name}")

    print()
    print("CURRENT ACTIVITY")
    print(f"  Messages: {report.get('total_messages', 0)}")
    print(f"  Active members: {report.get('unique_members', 0)}")

    metrics = report.get("metrics", {})

    for label, key, value_key in (
        ("Busiest channel", "busiest_channel", "channel_id"),
        ("Busiest day", "busiest_day", "date"),
        ("Busiest hour", "busiest_hour", "hour"),
    ):
        item = metrics.get(key)

        if isinstance(item, dict):
            print(f"  {label}: {item.get(value_key)}")

    print(f"  Activity trend: {metrics.get('daily_trend', 'unknown')}")

    structure = report.get("deterministic_structure", {})
    print()
    print("DETERMINISTIC STRUCTURE FINDINGS")

    for finding in structure.get("findings", [])[:10]:
        if isinstance(finding, dict):
            print(f"  - {finding.get('title', 'Finding')}")
            print(f"    {finding.get('description', '')}")

    print()
    print("HISTORICAL COMPARISON")

    if historical_comparison.get("available"):
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
        print("  No previous report available.")

    objectives = analysis.get("objectives", [])
    print()
    print(f"OBJECTIVES ({len(objectives)})")

    for index, objective in enumerate(objectives, start=1):
        if not isinstance(objective, dict):
            continue

        print(
            f"  {index}. Objective #{objective.get('id', '?')}: "
            f"{objective.get('objective', 'Unknown objective')}"
        )
        print(f"     Status: {objective.get('status', 'unknown')}")
        print(f"     Assessment: {objective.get('assessment', '')}")
        print(f"     Evidence: {objective.get('evidence', '')}")

    print()
    print("AI SUMMARY")
    print(analysis.get("summary", "No summary provided."))

    observations = analysis.get("observations", [])
    print()
    print(f"OBSERVATIONS ({len(observations)})")

    for index, observation in enumerate(observations, start=1):
        if not isinstance(observation, dict):
            continue

        print(f"  {index}. {observation.get('title', 'Observation')}")
        print(f"     {observation.get('description', '')}")
        print(f"     Evidence: {observation.get('evidence', '')}")

    proposals = analysis.get("proposals", [])
    print()
    print(f"PROPOSALS ({len(proposals)})")

    for index, proposal in enumerate(proposals, start=1):
        if not isinstance(proposal, dict):
            continue

        print(f"  {index}. {proposal.get('title', 'Proposal')}")
        print(f"     {proposal.get('description', '')}")
        print(f"     Action: {proposal.get('action')}")

    print()
    print("========================================")
    print()


async def analyze_server(guild_id: int, days: int = 7, guild=None):
    report = build_activity_report(guild_id, days)

    print_activity_report(report, guild)

    structure_result = {
        "available": False,
        "snapshot": {},
        "findings": [],
        "finding_count": 0,
        "summary": {
            "channel_count": 0,
            "category_count": 0,
            "finding_count": 0,
        },
    }

    if guild is not None:
        try:
            structure_result = analyze_server_structure(guild)
            structure_result["available"] = True

            print(
                "ANALYTICS: Deterministic intelligence found "
                f"{structure_result['finding_count']} potential issue(s).",
                flush=True,
            )
        except Exception as exc:
            print(
                f"ANALYTICS: Deterministic intelligence failed: {exc!r}",
                flush=True,
            )

    report["deterministic_structure"] = structure_result

    previous_report = get_previous_analysis_report(guild_id)
    historical_comparison = build_historical_comparison(
        report, previous_report
    )

    memories = get_memories(
        guild_id=guild_id,
        memory_type="observation",
        limit=20,
    )
    memory_context = build_memory_context(memories)

    print(
        f"ANALYTICS: Loaded {memory_context['count']} memory item(s).",
        flush=True,
    )

    objective_context = build_objective_context(guild_id)

    print(
        f"ANALYTICS: Loaded {len(objective_context)} active objective(s).",
        flush=True,
    )

    prompt = build_analysis_prompt(
        report,
        historical_comparison,
        memory_context,
        objective_context,
    )

    provider_name, raw_response = await ask_with_fallback(prompt)

    if raw_response is None:
        print(
            "ANALYTICS: All AI providers failed. "
            "Deterministic findings remain available.",
            flush=True,
        )

        return {
            "provider": None,
            "report": report,
            "analysis": None,
            "historical_comparison": historical_comparison,
        }

    print(
        f"ANALYTICS: {provider_name} returned a response.",
        flush=True,
    )

    try:
        analysis = json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        print("ANALYTICS: AI returned invalid JSON.", flush=True)

        return {
            "provider": provider_name,
            "report": report,
            "analysis": None,
            "historical_comparison": historical_comparison,
        }

    if not validate_analysis(analysis):
        print("ANALYTICS: AI analysis failed validation.", flush=True)

        return {
            "provider": provider_name,
            "report": report,
            "analysis": None,
            "historical_comparison": historical_comparison,
        }

    saved_memories = save_analysis_memories(guild_id, analysis)

    print(
        f"ANALYTICS: Saved {saved_memories} observation(s) to memory.",
        flush=True,
    )

    saved_assessments = save_analysis_objective_assessments(
        guild_id, analysis
    )

    print(
        f"ANALYTICS: Saved {saved_assessments} objective assessment(s).",
        flush=True,
    )

    record_analysis_report(
        guild_id=guild_id,
        period_days=days,
        total_messages=report["total_messages"],
        unique_members=report["unique_members"],
        provider=provider_name,
        analysis_json=json.dumps(analysis),
    )

    print("ANALYTICS: Analysis report saved.", flush=True)

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