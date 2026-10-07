import discord
from discord import app_commands
from discord.ext import commands

from analytics.analyzer import analyze_server
from analytics.proposals import (
    process_analytics_proposals,
)


class Analytics(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

    @app_commands.command(
        name="analytics",
        description="Analyze server activity and generate improvement proposals.",
    )
    async def analytics(
        self,
        interaction: discord.Interaction,
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )

            return

        if interaction.user.id != interaction.guild.owner_id:

            await interaction.response.send_message(
                "Only the server owner can request server analytics.",
                ephemeral=True,
            )

            return

        await interaction.response.defer()

        result = await analyze_server(
            interaction.guild.id,
            days=7,
        )

        analysis = result.get(
            "analysis"
        )

        provider = result.get(
            "provider"
        )

        if analysis is None:

            await interaction.followup.send(
                "The AI analysis could not be generated. "
                "All configured AI providers failed."
            )

            return

        report = result["report"]

        metrics = report.get(
            "metrics",
            {},
        )

        historical_comparison = result.get(
            "historical_comparison",
            {},
        )

        summary = analysis.get(
            "summary",
            "No summary was provided.",
        )

        embed = discord.Embed(
            title="📊 Server Analytics",
            description=summary,
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="📅 Reporting Period",
            value=f"Last {report['period_days']} days",
            inline=True,
        )

        embed.add_field(
            name="💬 Messages",
            value=str(
                report["total_messages"]
            ),
            inline=True,
        )

        embed.add_field(
            name="👥 Active Members",
            value=str(
                report["unique_members"]
            ),
            inline=True,
        )

        average_messages = metrics.get(
            "average_messages_per_member"
        )

        if average_messages is not None:

            embed.add_field(
                name="📊 Avg. Messages / Member",
                value=str(
                    average_messages
                ),
                inline=True,
            )

        busiest_channel = metrics.get(
            "busiest_channel"
        )

        if busiest_channel:

            channel_id = busiest_channel.get(
                "channel_id"
            )

            channel = interaction.guild.get_channel(
                channel_id
            )

            if channel:

                channel_value = channel.mention

            else:

                channel_value = f"<#{channel_id}>"

            embed.add_field(
                name="🔥 Busiest Channel",
                value=channel_value,
                inline=True,
            )

        busiest_day = metrics.get(
            "busiest_day"
        )

        if busiest_day:

            embed.add_field(
                name="📅 Busiest Day",
                value=busiest_day.get(
                    "date",
                    "Unknown",
                ),
                inline=True,
            )

        busiest_hour = metrics.get(
            "busiest_hour"
        )

        if busiest_hour:

            embed.add_field(
                name="🕐 Busiest Hour",
                value=(
                    f"{busiest_hour.get('hour', '?')}:00 UTC"
                ),
                inline=True,
            )

        daily_trend = metrics.get(
            "daily_trend",
            "unknown",
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

        embed.add_field(
            name="📈 Activity Trend",
            value=trend_labels.get(
                daily_trend,
                "❓ Unknown",
            ),
            inline=True,
        )

        if historical_comparison.get(
            "available"
        ):

            message_change = historical_comparison.get(
                "message_change_percent"
            )

            member_change = historical_comparison.get(
                "member_change_percent"
            )

            previous_messages = historical_comparison.get(
                "previous_total_messages"
            )

            previous_members = historical_comparison.get(
                "previous_unique_members"
            )

            current_messages = historical_comparison.get(
                "current_total_messages"
            )

            current_members = historical_comparison.get(
                "current_unique_members"
            )

            if message_change is None:

                message_change_text = "New activity"

            elif message_change > 0:

                message_change_text = (
                    f"📈 +{message_change}%"
                )

            elif message_change < 0:

                message_change_text = (
                    f"📉 {message_change}%"
                )

            else:

                message_change_text = "➡️ 0%"

            if member_change is None:

                member_change_text = "New activity"

            elif member_change > 0:

                member_change_text = (
                    f"📈 +{member_change}%"
                )

            elif member_change < 0:

                member_change_text = (
                    f"📉 {member_change}%"
                )

            else:

                member_change_text = "➡️ 0%"

            embed.add_field(
                name="📈 Message Change",
                value=(
                    f"Previous: {previous_messages}\n"
                    f"Current: {current_messages}\n"
                    f"Change: {message_change_text}"
                ),
                inline=True,
            )

            embed.add_field(
                name="👥 Member Change",
                value=(
                    f"Previous: {previous_members}\n"
                    f"Current: {current_members}\n"
                    f"Change: {member_change_text}"
                ),
                inline=True,
            )

        observations = analysis.get(
            "observations",
            [],
        )

        if observations:

            observation_text = ""

            for observation in observations:

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

                observation_text += (
                    f"**{title}**\n"
                    f"{description}\n"
                )

                if evidence:

                    observation_text += (
                        f"*Evidence: {evidence}*\n"
                    )

                observation_text += "\n"

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

            for proposal in proposals:

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

        await interaction.followup.send(
            embed=embed
        )

        await process_analytics_proposals(
            guild=interaction.guild,
            proposals=proposals,
            send_function=interaction.followup.send,
        )


async def setup(
    bot: commands.Bot,
):

    await bot.add_cog(
        Analytics(bot)
    )