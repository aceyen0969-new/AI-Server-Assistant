import asyncio

import discord

from analytics.analyzer import analyze_server
from analytics.proposals import process_analytics_proposals
from onboarding import ensure_server_setup, get_server_config


ANALYTICS_INTERVAL = 86400


def get_analytics_channel(guild):
    config = get_server_config(guild.id)

    if not config:
        return None

    channel_id = config.get("analytics_channel_id")

    if not channel_id:
        return None

    channel = guild.get_channel(int(channel_id))

    if isinstance(channel, discord.TextChannel):
        return channel

    return None


async def resolve_analytics_channel(guild):
    analytics_channel = get_analytics_channel(guild)

    if analytics_channel is not None:
        return analytics_channel

    print(
        "ANALYTICS SCHEDULER: Saved analytics channel is missing "
        f"for {guild.name}. Running onboarding setup.",
        flush=True,
    )

    try:
        await ensure_server_setup(guild)
    except Exception as exc:
        print(
            "ANALYTICS SCHEDULER: Onboarding recovery failed "
            f"for {guild.name}: {exc!r}",
            flush=True,
        )
        return None

    analytics_channel = get_analytics_channel(guild)

    if analytics_channel is not None:
        print(
            "ANALYTICS SCHEDULER: Resolved analytics channel "
            f"for {guild.name}: #{analytics_channel.name} "
            f"(channel_id={analytics_channel.id})",
            flush=True,
        )
        return analytics_channel

    print(
        "ANALYTICS SCHEDULER: No configured analytics channel "
        f"could be resolved for {guild.name}.",
        flush=True,
    )

    return None


def get_result_value(result, *keys, default=None):
    for key in keys:
        value = result.get(key)

        if value is not None:
            return value

    return default


def format_findings(result):
    findings = get_result_value(
        result,
        "deterministic_findings",
        "findings",
        default=[],
    )

    if not findings:
        structure = result.get("deterministic_structure", {})

        if isinstance(structure, dict):
            findings = structure.get("findings", [])

    if not findings:
        return "No deterministic structure findings."

    lines = []

    for finding in findings[:5]:
        if isinstance(finding, dict):
            title = (
                finding.get("title")
                or finding.get("name")
                or finding.get("type")
                or "Finding"
            )

            description = (
                finding.get("description")
                or finding.get("reason")
                or ""
            )

            line = f"• **{title}**"

            if description:
                line += f"\n  {description}"

            lines.append(line)
        else:
            lines.append(f"• {finding}")

    if len(findings) > 5:
        lines.append(
            f"• And {len(findings) - 5} more finding(s)."
        )

    return "\n".join(lines)[:1024]


def format_observations(observations):
    if not observations:
        return "No AI observations returned."

    lines = []

    for observation in observations[:5]:
        if isinstance(observation, dict):
            title = (
                observation.get("title")
                or observation.get("name")
                or observation.get("type")
                or "Observation"
            )

            description = (
                observation.get("description")
                or observation.get("details")
                or observation.get("observation")
                or ""
            )

            line = f"• **{title}**"

            if description:
                line += f"\n  {description}"

            lines.append(line)
        else:
            lines.append(f"• {observation}")

    if len(observations) > 5:
        lines.append(
            f"• And {len(observations) - 5} more observation(s)."
        )

    return "\n".join(lines)[:1024]


def format_proposals(proposals):
    if not proposals:
        return "No proposals generated."

    lines = []

    for proposal in proposals[:5]:
        if isinstance(proposal, dict):
            title = (
                proposal.get("title")
                or proposal.get("name")
                or proposal.get("action")
                or "Suggested improvement"
            )

            description = (
                proposal.get("description")
                or proposal.get("reason")
                or proposal.get("details")
                or ""
            )

            line = f"• **{title}**"

            if description:
                line += f"\n  {description}"

            lines.append(line)
        else:
            lines.append(f"• {proposal}")

    if len(proposals) > 5:
        lines.append(
            f"• And {len(proposals) - 5} more proposal(s)."
        )

    return "\n".join(lines)[:1024]


async def run_analytics_cycle(guild):
    print(
        f"ANALYTICS SCHEDULER: Running analytics for {guild.name}.",
        flush=True,
    )

    analytics_channel = await resolve_analytics_channel(guild)

    if analytics_channel is None:
        print(
            "ANALYTICS SCHEDULER: Skipping report because no "
            f"analytics channel is available in {guild.name}.",
            flush=True,
        )
        return

    try:
        result = await analyze_server(
            guild.id,
            days=7,
            guild=guild,
        )

        if not isinstance(result, dict):
            print(
                "ANALYTICS SCHEDULER: Analysis returned an "
                f"unexpected result for {guild.name}: "
                f"{type(result).__name__}",
                flush=True,
            )
            return

        summary = get_result_value(
            result,
            "summary",
            "ai_summary",
            default="Analytics analysis completed.",
        )

        provider = get_result_value(
            result,
            "provider",
            "ai_provider",
            default="Unknown",
        )

        observations = result.get("observations", [])
        proposals = result.get("proposals", [])

        total_messages = get_result_value(
            result,
            "total_messages",
            "message_count",
            default=0,
        )

        active_members = get_result_value(
            result,
            "unique_members",
            "active_members",
            default=0,
        )

        embed = discord.Embed(
            title="📊 Automatic Server Analytics",
            description=str(summary)[:4096],
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="📅 Reporting Period",
            value="Last 7 days",
            inline=True,
        )

        embed.add_field(
            name="🤖 AI Provider",
            value=str(provider)[:1024],
            inline=True,
        )

        embed.add_field(
            name="💬 Messages",
            value=str(total_messages),
            inline=True,
        )

        embed.add_field(
            name="👥 Active Members",
            value=str(active_members),
            inline=True,
        )

        embed.add_field(
            name="🔎 Deterministic Findings",
            value=format_findings(result),
            inline=False,
        )

        if observations:
            embed.add_field(
                name="🧠 AI Observations",
                value=format_observations(observations),
                inline=False,
            )

        if proposals:
            embed.add_field(
                name="💡 Proposals",
                value=format_proposals(proposals),
                inline=False,
            )

        embed.set_footer(
            text=f"AI provider: {provider}"
        )

        try:
            await analytics_channel.send(embed=embed)

            print(
                "ANALYTICS SCHEDULER: Report sent to "
                f"#{analytics_channel.name} "
                f"(channel_id={analytics_channel.id}) "
                f"in {guild.name}.",
                flush=True,
            )

        except discord.HTTPException as exc:
            print(
                "ANALYTICS SCHEDULER: Failed to send report "
                f"to {guild.name}: {exc!r}",
                flush=True,
            )
            return

        if proposals:
            print(
                "ANALYTICS SCHEDULER: Processing "
                f"{len(proposals)} proposal(s).",
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
                    "ANALYTICS SCHEDULER: Proposal processing "
                    f"failed for {guild.name}: {exc!r}",
                    flush=True,
                )

        print(
            "ANALYTICS SCHEDULER: Analytics cycle completed "
            f"for {guild.name}.",
            flush=True,
        )

    except Exception as exc:
        print(
            "ANALYTICS SCHEDULER: Analytics cycle failed "
            f"for {guild.name}: {exc!r}",
            flush=True,
        )


async def analytics_scheduler(bot):
    await bot.wait_until_ready()

    print(
        "ANALYTICS SCHEDULER: Started. "
        f"Interval={ANALYTICS_INTERVAL} seconds.",
        flush=True,
    )

    while not bot.is_closed():
        for guild in bot.guilds:
            if bot.is_closed():
                break

            try:
                await run_analytics_cycle(guild)

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                print(
                    "ANALYTICS SCHEDULER: Unexpected error "
                    f"in {guild.name}: {exc!r}",
                    flush=True,
                )

        try:
            await asyncio.sleep(ANALYTICS_INTERVAL)

        except asyncio.CancelledError:
            raise