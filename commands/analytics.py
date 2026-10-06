import discord
from discord import app_commands
from discord.ext import commands

from analytics.analyzer import analyze_server


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
                name="🕕 Busiest Hour",
                value=f"{busiest_hour.get('hour', '?')}:00 UTC",
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
            "insufficient_data": "⚠️ Insufficient data",
            "unknown": "❓ Unknown",
        }

        embed.add_field(
            name="📈 Daily Trend",
            value=trend_labels.get(
                daily_trend,
                daily_trend,
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

                title = observation.get(
                    "title",
                    "Observation",
                )

                description = observation.get(
                    "description",
                    "",
                )

                observation_text += (
                    f"**{title}**\n"
                    f"{description}\n\n"
                )

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


async def setup(
    bot: commands.Bot,
):

    await bot.add_cog(
        Analytics(bot)
    )