
import asyncio

import discord

from analytics.analyzer import analyze_server
from analytics.database import DATABASE_PATH, get_message_count
from analytics.proposals import process_analytics_proposals
from onboarding import (
    get_server_config,
    save_server_config,
)


ANALYTICS_INTERVAL = 86400
ANALYTICS_CHANNEL_ALIASES = ("quasar-reports", "analytics")


def resolve_analytics_channel(guild):
    config = get_server_config(guild.id) or {}
    saved_channel_id = config.get("analytics_channel_id")

    if saved_channel_id:
        saved_channel = guild.get_channel(saved_channel_id)

        if isinstance(saved_channel, discord.TextChannel):
            if (
                saved_channel.name == "analytics"
                and saved_channel.name == "analytics"
            ):
                preferred_channel = discord.utils.get(
                    guild.text_channels,
                    name="quasar-reports",
                )

                if preferred_channel is not None:
                    print(
                        "ANALYTICS SCHEDULER: Migrating saved analytics "
                        f"channel from #{saved_channel.name} to "
                        f"#{preferred_channel.name} in {guild.name}.",
                        flush=True,
                    )
                    saved_channel = preferred_channel

                    save_server_config(
                        guild.id,
                        analytics_channel_id=saved_channel.id,
                    )

            return saved_channel

    for channel_name in ANALYTICS_CHANNEL_ALIASES:
        channel = discord.utils.get(
            guild.text_channels,
            name=channel_name,
        )

        if channel is not None:
            save_server_config(
                guild.id,
                analytics_channel_id=channel.id,
            )

            print(
                "ANALYTICS SCHEDULER: Selected "
                f"#{channel.name} as the analytics channel "
                f"for {guild.name}.",
                flush=True,
            )

            return channel

    return None


def format_structure_findings(structure_result):
    if not isinstance(structure_result, dict):
        return "Deterministic findings are unavailable."

    if not structure_result.get("available", True):
        return "Deterministic structure analysis is unavailable."

    findings = structure_result.get("findings", [])

    if not isinstance(findings, list):
        return "Deterministic findings are unavailable."

    if not findings:
        return "No potential organization issues were detected."

    lines = []

    for finding in findings[:5]:
        if not isinstance(finding, dict):
            continue

        title = str(finding.get("title", "Finding"))
        description = str(
            finding.get("description", "No description available.")
        )
        recommendation = str(
            finding.get("recommendation", "Review if appropriate.")
        )

        lines.append(
            f"**{title[:200]}**\n"
            f"{description[:300]}\n"
            f"*Suggestion: {recommendation[:250]}*"
        )

    if not lines:
        return "No readable findings were produced."

    result = "\n\n".join(lines)

    if len(findings) > 5:
        result += f"\n\n*And {len(findings) - 5} more finding(s).*"

    return result[:1024]


async def run_analytics_cycle(guild: discord.Guild):
    print(
        f"ANALYTICS DEBUG: Guild={guild.name!r}, "
        f"id={guild.id}, "
        f"channels={len(guild.channels)}, "
        f"text_channels={len(guild.text_channels)}, "
        f"categories={len(guild.categories)}, "
        f"members={guild.member_count}",
        flush=True,
    )

    print(
        f"ANALYTICS DATABASE DEBUG: path={DATABASE_PATH}",
        flush=True,
    )

    try:
        database_total = get_message_count(guild.id)
        database_seven_days = get_message_count(guild.id, 7)

        print(
            "ANALYTICS DATABASE DEBUG: "
            f"guild_id={guild.id}, "
            f"total_messages={database_total}, "
            f"last_7_days={database_seven_days}",
            flush=True,
        )
    except Exception as exc:
        print(
            "ANALYTICS DATABASE DEBUG: Direct database count failed.",
            flush=True,
        )
        print(repr(exc), flush=True)

    print(
        "ANALYTICS SCHEDULER: Running analytics...",
        flush=True,
    )

    result = await analyze_server(
        guild.id,
        days=7,
        guild=guild,
    )

    if not isinstance(result, dict):
        print(
            "ANALYTICS SCHEDULER: Invalid analytics result.",
            flush=True,
        )
        return

    analysis = result.get("analysis")
    provider = result.get("provider")
    report = result.get("report", {})

    if not isinstance(report, dict):
        report = {}

    print(
        "ANALYTICS REPORT DEBUG: "
        f"guild_id={guild.id}, "
        f"report_total_messages={report.get('total_messages')!r}, "
        f"report_unique_members={report.get('unique_members')!r}",
        flush=True,
    )

    structure_result = report.get(
        "deterministic_structure",
        {},
    )

    if analysis is not None:
        print(
            f"ANALYTICS SCHEDULER: Analysis completed using {provider}.",
            flush=True,
        )

        summary = analysis.get(
            "summary",
            "No summary available.",
        )

        if not isinstance(summary, str):
            summary = str(summary)
    else:
        print(
            "ANALYTICS SCHEDULER: AI analysis unavailable. "
            "Publishing deterministic findings if available.",
            flush=True,
        )

        summary = (
            "AI analysis was unavailable for this cycle. "
            "Deterministic server structure findings are shown below."
        )

    analytics_channel = resolve_analytics_channel(guild)

    if analytics_channel is None:
        print(
            "ANALYTICS SCHEDULER: No analytics destination found "
            f"in {guild.name}. Create #quasar-reports or #analytics.",
            flush=True,
        )
        return

    embed = discord.Embed(
        title="📊 Automatic Server Analytics",
        description=summary[:4096],
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="📅 Reporting Period",
        value="Last 7 days",
        inline=True,
    )

    embed.add_field(
        name="🤖 AI Provider",
        value=str(provider or "Unavailable")[:1024],
        inline=True,
    )

    if report.get("total_messages") is not None:
        embed.add_field(
            name="💬 Messages",
            value=str(report["total_messages"])[:1024],
            inline=True,
        )

    if report.get("unique_members") is not None:
        embed.add_field(
            name="👥 Active Members",
            value=str(report["unique_members"])[:1024],
            inline=True,
        )

    structure_summary = (
        structure_result.get("summary", {})
        if isinstance(structure_result, dict)
        else {}
    )

    finding_count = structure_summary.get("finding_count", 0)

    embed.add_field(
        name=f"🧠 Deterministic Findings ({finding_count})",
        value=format_structure_findings(structure_result),
        inline=False,
    )

    proposals = []

    if isinstance(analysis, dict):
        observations = analysis.get("observations", [])

        if isinstance(observations, list) and observations:
            observation_items = []

            for observation in observations[:5]:
                if not isinstance(observation, dict):
                    continue

                title = str(observation.get("title", "Observation"))
                description = str(
                    observation.get("description", "No description.")
                )

                observation_items.append(
                    f"**{title[:200]}**\n{description[:500]}"
                )

            observation_text = "\n\n".join(observation_items)

            if observation_text:
                embed.add_field(
                    name="🔎 AI Observations",
                    value=observation_text[:1024],
                    inline=False,
                )

        proposals = analysis.get("proposals", [])

        if not isinstance(proposals, list):
            proposals = []

        if proposals:
            proposal_items = []

            for proposal in proposals[:5]:
                if not isinstance(proposal, dict):
                    continue

                title = str(proposal.get("title", "Proposal"))
                description = str(
                    proposal.get("description", "No description.")
                )

                proposal_items.append(
                    f"**{title[:200]}**\n{description[:500]}"
                )

            proposal_text = "\n\n".join(proposal_items)

            if proposal_text:
                embed.add_field(
                    name="💡 AI Proposals",
                    value=proposal_text[:1024],
                    inline=False,
                )

    embed.set_footer(
        text=f"AI provider: {provider or 'Unavailable'}"
    )

    try:
        await analytics_channel.send(embed=embed)

        print(
            "ANALYTICS SCHEDULER: Report sent to "
            f"#{analytics_channel.name} "
            f"(channel_id={analytics_channel.id}).",
            flush=True,
        )

    except discord.HTTPException as exc:
        print(
            "ANALYTICS SCHEDULER: Failed to send report.",
            flush=True,
        )
        print(repr(exc), flush=True)
        return

    if analysis is None:
        print(
            "ANALYTICS SCHEDULER: Skipping proposal processing "
            "because valid AI analysis is unavailable.",
            flush=True,
        )
        return

    print(
        f"ANALYTICS SCHEDULER: Processing {len(proposals)} proposal(s).",
        flush=True,
    )

    try:
        await process_analytics_proposals(
            guild=guild,
            proposals=proposals,
            send_function=analytics_channel.send,
        )
    except Exception as exc:
        print(
            "ANALYTICS SCHEDULER: Proposal processing failed.",
            flush=True,
        )
        print(repr(exc), flush=True)
        return

    print(
        "ANALYTICS SCHEDULER: Analytics cycle completed.",
        flush=True,
    )


async def analytics_scheduler(bot):
    while True:
        for guild in bot.guilds:
            try:
                await run_analytics_cycle(guild)
            except Exception as exc:
                print(
                    f"ANALYTICS SCHEDULER: Guild {guild.id} failed.",
                    flush=True,
                )
                print(repr(exc), flush=True)

        await asyncio.sleep(ANALYTICS_INTERVAL)
