import asyncio

import discord

from analytics.analyzer import analyze_server
from analytics.proposals import (
    process_analytics_proposals,
)


ANALYTICS_INTERVAL = 86400


async def run_analytics_cycle(
    guild: discord.Guild,
):
    """Run one scheduled analytics cycle."""

    print(
        "ANALYTICS SCHEDULER: Running analytics..."
    )

    result = await analyze_server(
        guild.id,
        days=7,
        guild=guild,
    )

    analysis = result.get(
        "analysis"
    )

    provider = result.get(
        "provider"
    )

    if analysis is None:

        print(
            "ANALYTICS SCHEDULER: "
            "AI analysis failed."
        )

        return

    print(
        "ANALYTICS SCHEDULER: "
        f"Analysis completed using {provider}."
    )

    summary = analysis.get(
        "summary",
        "No summary available.",
    )

    print(
        "ANALYTICS SCHEDULER: "
        f"Summary: {summary}"
    )

    # ========================================
    # FIND ANALYTICS CHANNEL
    # ========================================

    analytics_channel = discord.utils.get(
        guild.text_channels,
        name="analytics",
    )

    print(
        "ANALYTICS SCHEDULER: "
        f"Found analytics channel: {analytics_channel}"
    )

    if analytics_channel is None:

        print(
            "ANALYTICS SCHEDULER: "
            f"No #analytics channel found in {guild.name}."
        )

        return

    # ========================================
    # BUILD REPORT EMBED
    # ========================================

    embed = discord.Embed(
        title="📊 Automatic Server Analytics",
        description=summary,
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="📅 Reporting Period",
        value="Last 7 days",
        inline=True,
    )

    embed.add_field(
        name="🤖 AI Provider",
        value=provider or "Unknown",
        inline=True,
    )

    observations = analysis.get(
        "observations",
        [],
    )

    if observations:

        observation_text = ""

        for observation in observations[:5]:

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
                "No description.",
            )

            observation_text += (
                f"**{title}**\n"
                f"{description}\n\n"
            )

        if observation_text:

            embed.add_field(
                name="🔎 Observations",
                value=observation_text[:1024],
                inline=False,
            )

    proposals = analysis.get(
        "proposals",
        [],
    )

    if proposals:

        proposal_text = ""

        for proposal in proposals[:5]:

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
                "No description.",
            )

            proposal_text += (
                f"**{title}**\n"
                f"{description}\n\n"
            )

        if proposal_text:

            embed.add_field(
                name="💡 Proposals",
                value=proposal_text[:1024],
                inline=False,
            )

    embed.set_footer(
        text=f"AI provider: {provider}"
    )

    # ========================================
    # SEND REPORT
    # ========================================

    try:

        await analytics_channel.send(
            embed=embed
        )

        print(
            "ANALYTICS SCHEDULER: "
            f"Report sent to #{analytics_channel.name}."
        )

    except discord.HTTPException as e:

        print(
            "ANALYTICS SCHEDULER: "
            "Failed to send report."
        )

        print(
            repr(e)
        )

        return

    # ========================================
    # PROCESS ACTIONABLE PROPOSALS
    # ========================================

    await process_analytics_proposals(
        guild=guild,
        proposals=proposals,
        send_function=analytics_channel.send,
    )


async def analytics_scheduler(
    bot,
):
    """Run scheduled analytics for all connected servers."""

    while True:

        for guild in bot.guilds:

            try:

                await run_analytics_cycle(
                    guild
                )

            except Exception as e:

                print(
                    "ANALYTICS SCHEDULER: "
                    f"Guild {guild.id} failed."
                )

                print(
                    repr(e)
                )

        await asyncio.sleep(
            ANALYTICS_INTERVAL
        )