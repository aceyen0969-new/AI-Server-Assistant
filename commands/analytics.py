import uuid

import discord
from discord import app_commands
from discord.ext import commands

from analytics.analyzer import analyze_server

from security.actions import (
    ActionRequest,
    evaluate_action,
)

from security.approval import (
    create_approval_request,
)

from security.approval_view import (
    ApprovalView,
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

        # ========================================
        # ACTIONABLE PROPOSALS
        # ========================================

        for proposal in proposals:

            if not isinstance(
                proposal,
                dict,
            ):
                continue

            action = proposal.get(
                "action"
            )

            # Informational proposal.
            # No Discord action is created.
            if action is None:
                continue

            if not isinstance(
                action,
                dict,
            ):
                continue

            action_type = action.get(
                "action"
            )

            # ========================================
            # CREATE CHANNEL
            # ========================================

            if action_type == "create_channel":

                name = action.get(
                    "name"
                )

                channel_type = action.get(
                    "channel_type"
                )

                # Validate the AI-generated channel name.

                if not isinstance(
                    name,
                    str,
                ):
                    continue

                name = name.strip()

                if not name:
                    continue

                if len(name) > 100:
                    continue

                # Only allow channel types supported
                # by the action executor.

                if channel_type not in (
                    "text",
                    "voice",
                ):
                    continue

                # Prevent the AI from proposing a
                # channel that already exists.

                existing_channel = discord.utils.get(
                    interaction.guild.channels,
                    name=name,
                )

                if existing_channel is not None:
                    continue

                title = proposal.get(
                    "title",
                    "Create Channel",
                )

                description = proposal.get(
                    "description",
                    "",
                )

                reason = proposal.get(
                    "reason",
                    description,
                )

                # ====================================
                # SECURITY ACTION REQUEST
                # ====================================

                action_request = ActionRequest(
                    action="create_channel",
                    target_name=name,
                    reason=reason,
                    data={
                        "name": name,
                        "channel_type": channel_type,
                    },
                )

                decision = evaluate_action(
                    action_request
                )

                # If the security system completely
                # rejects the action, do nothing.

                if (
                    not decision["allowed"]
                    and not decision["requires_approval"]
                ):
                    print(
                        "ANALYTICS: Security rejected "
                        "create_channel proposal."
                    )
                    continue

                # Analytics proposals should not execute
                # automatically. They must go through the
                # approval system.

                if not decision["requires_approval"]:

                    print(
                        "ANALYTICS: create_channel does not "
                        "require approval. Skipping automatic execution."
                    )

                    continue

                # ====================================
                # CREATE APPROVAL REQUEST
                # ====================================

                request_id = str(
                    uuid.uuid4()
                )

                create_approval_request(
                    request_id=request_id,
                    action="create_channel",
                    target_name=name,
                    reason=reason,
                    data={
                        "name": name,
                        "channel_type": channel_type,
                    },
                )

                # ====================================
                # PROPOSAL EMBED
                # ====================================

                proposal_embed = discord.Embed(
                    title="💡 AI Server Improvement Proposal",
                    description=(
                        f"**Proposal:** {title}\n\n"
                        f"{description}\n\n"
                        f"**Reason:** {reason}\n\n"
                        f"**Action:** `create_channel`\n"
                        f"**Name:** `{name}`\n"
                        f"**Type:** `{channel_type}`\n\n"
                        "This change requires server-owner approval."
                    ),
                    color=discord.Color.orange(),
                )

                proposal_embed.set_footer(
                    text="AI Server Assistant"
                )

                # ====================================
                # EXISTING APPROVAL VIEW
                # ====================================

                view = ApprovalView(
                    request_id=request_id,
                    allowed_user_id=interaction.guild.owner_id,
                    guild=interaction.guild,
                )

                await interaction.followup.send(
                    embed=proposal_embed,
                    view=view,
                )

                continue

            # ========================================
            # UNSUPPORTED ACTION
            # ========================================

            print(
                "ANALYTICS: Ignoring unsupported "
                f"proposal action: {action_type}"
            )


async def setup(
    bot: commands.Bot,
):

    await bot.add_cog(
        Analytics(bot)
    )