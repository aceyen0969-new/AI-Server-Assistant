
import asyncio

import discord

from analytics.analyzer import analyze_server
from analytics.proposals import process_analytics_proposals


ANALYTICS_INTERVAL = 86400


async def run_analytics_cycle(guild: discord.Guild):
    """Run one scheduled analytics cycle."""

    print(
        "ANALYTICS SCHEDULER: Running analytics...",
        flush=True,
    )

    result = await analyze_server(
        guild.id,
        days=7,
        guild=guild,
    )

    analysis = result.get("analysis")
    provider = result.get("provider")

    if analysis is None:
        print(
            "ANALYTICS SCHEDULER: AI analysis failed.",
            flush=True,
        )
        return

    print(
        f"ANALYTICS SCHEDULER: Analysis completed using {provider}.",
        flush=True,
    )

    summary = analysis.get("summary", "No summary available.")

    if not isinstance(summary, str):
        summary = str(summary)

    print(
        f"ANALYTICS SCHEDULER: Summary: {summary}",
        flush=True,
    )

    analytics_channel = discord.utils.get(
        guild.text_channels,
        name="analytics",
    )

    print(
        f"ANALYTICS SCHEDULER: Found analytics channel: {analytics_channel}",
        flush=True,
    )

    if analytics_channel is None:
        print(
            f"ANALYTICS SCHEDULER: No #analytics channel found in {guild.name}.",
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
        value=str(provider or "Unknown")[:1024],
        inline=True,
    )

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
                f"**{title}**\n{description}"
            )

        observation_text = "\n\n".join(observation_items)

        if observation_text:
            embed.add_field(
                name="🔎 Observations",
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
                f"**{title}**\n{description}"
            )

        proposal_text = "\n\n".join(proposal_items)

        if proposal_text:
            embed.add_field(
                name="💡 Proposals",
                value=proposal_text[:1024],
                inline=False,
            )

    embed.set_footer(
        text=f"AI provider: {provider or 'Unknown'}"
    )

    print(
        f"ANALYTICS SCHEDULER: Sending report to #{analytics_channel.name}.",
        flush=True,
    )

    try:
        await analytics_channel.send(embed=embed)

        print(
            f"ANALYTICS SCHEDULER: Report sent to #{analytics_channel.name}.",
            flush=True,
        )

    except discord.HTTPException as e:
        print(
            "ANALYTICS SCHEDULER: Failed to send report.",
            flush=True,
        )
        print(repr(e), flush=True)
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
    except Exception as e:
        print(
            "ANALYTICS SCHEDULER: Proposal processing failed.",
            flush=True,
        )
        print(repr(e), flush=True)
        return

    print(
        "ANALYTICS SCHEDULER: Analytics cycle completed.",
        flush=True,
    )


async def analytics_scheduler(bot):
    """Run scheduled analytics for all connected servers."""

    while True:
        for guild in bot.guilds:
            try:
                await run_analytics_cycle(guild)
            except Exception as e:
                print(
                    f"ANALYTICS SCHEDULER: Guild {guild.id} failed.",
                    flush=True,
                )
                print(repr(e), flush=True)

        await asyncio.sleep(ANALYTICS_INTERVAL)