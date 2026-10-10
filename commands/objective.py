import discord
from discord import app_commands

from analytics.database import (
    create_objective,
    get_objectives,
    get_objective,
    update_objective,
    delete_objective,
    get_latest_objective_assessment,
    get_objective_assessments,
)


def truncate_text(value, limit):
    value = str(value or "")
    if len(value) <= limit:
        return value
    return value[:limit - 3] + "..."


def format_timestamp(value):
    if not value:
        return "Unknown"

    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=__import__("datetime").timezone.utc
            )

        return discord.utils.format_dt(parsed, style="f")
    except (ValueError, TypeError, OverflowError):
        return truncate_text(value, 100)


def assessment_color(status):
    colors = {
        "safe": discord.Color.green(),
        "at_risk": discord.Color.orange(),
        "insufficient_evidence": discord.Color.gold(),
    }
    return colors.get(status, discord.Color.blurple())


async def setup(bot):
    objective_group = app_commands.Group(
        name="objective",
        description="Manage Quasar server objectives.",
    )

    @objective_group.command(
        name="add",
        description="Add a persistent server objective.",
    )
    @app_commands.describe(
        objective="What you want Quasar to accomplish.",
        priority="Objective priority.",
        description="Optional additional details.",
    )
    @app_commands.choices(
        priority=[
            app_commands.Choice(name="Low", value="low"),
            app_commands.Choice(name="Normal", value="normal"),
            app_commands.Choice(name="High", value="high"),
        ]
    )
    async def objective_add(
        interaction: discord.Interaction,
        objective: str,
        priority: app_commands.Choice[str],
        description: str = "",
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        objective = objective.strip()
        description = description.strip()

        if not objective:
            await interaction.response.send_message(
                "The objective cannot be empty.",
                ephemeral=True,
            )
            return

        if len(objective) > 500:
            await interaction.response.send_message(
                "The objective must be 500 characters or fewer.",
                ephemeral=True,
            )
            return

        if len(description) > 1000:
            await interaction.response.send_message(
                "The description must be 1000 characters or fewer.",
                ephemeral=True,
            )
            return

        objective_id = create_objective(
            guild_id=guild.id,
            objective=objective,
            description=description,
            priority=priority.value,
        )

        embed = discord.Embed(
            title="Objective Added",
            description=(
                f"**Objective:** {objective}\n"
                f"**Priority:** `{priority.value}`\n"
                "**Status:** `active`"
            ),
            color=discord.Color.green(),
        )

        if description:
            embed.add_field(
                name="Description",
                value=truncate_text(description, 1024),
                inline=False,
            )

        embed.set_footer(text=f"Objective ID: {objective_id}")

        await interaction.response.send_message(embed=embed)

    @objective_group.command(
        name="list",
        description="List the server's objectives.",
    )
    @app_commands.describe(
        status="Filter objectives by status.",
    )
    @app_commands.choices(
        status=[
            app_commands.Choice(name="Active", value="active"),
            app_commands.Choice(name="Paused", value="paused"),
            app_commands.Choice(name="Completed", value="completed"),
        ]
    )
    async def objective_list(
        interaction: discord.Interaction,
        status: app_commands.Choice[str] | None = None,
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        objectives = get_objectives(
            guild_id=guild.id,
            status=status.value if status else None,
            limit=20,
        )

        if not objectives:
            await interaction.response.send_message(
                "No objectives were found.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Server Objectives",
            color=discord.Color.blurple(),
        )

        for item in objectives:
            value = (
                f"**Priority:** `{item['priority']}`\n"
                f"**Status:** `{item['status']}`"
            )

            description = item["description"] or ""

            if description:
                value += (
                    "\n**Details:** "
                    + truncate_text(description, 850)
                )

            embed.add_field(
                name=truncate_text(
                    f"#{item['id']} {item['objective']}",
                    256,
                ),
                value=truncate_text(value, 1024),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @objective_group.command(
        name="status",
        description="Show active objectives and their latest assessments.",
    )
    async def objective_status(
        interaction: discord.Interaction,
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        objectives = get_objectives(
            guild_id=guild.id,
            status="active",
            limit=20,
        )

        if not objectives:
            await interaction.response.send_message(
                "There are no active objectives to assess.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Objective Status",
            description=(
                "Latest saved assessments for active objectives. "
                "This command does not run a new assessment."
            ),
            color=discord.Color.blurple(),
        )

        for item in objectives:
            latest = get_latest_objective_assessment(
                objective_id=item["id"],
                guild_id=guild.id,
            )

            if latest is None:
                value = (
                    f"**Priority:** `{item['priority']}`\n"
                    "**Assessment:** `insufficient_evidence`\n"
                    "No assessment has been recorded yet."
                )
            else:
                status_value = latest["status"]
                value = (
                    f"**Priority:** `{item['priority']}`\n"
                    f"**Assessment:** `{status_value}`\n"
                    f"**Assessed:** "
                    f"{format_timestamp(latest['created_at'])}\n"
                    f"{truncate_text(latest['assessment'], 650)}"
                )

                evidence = latest.get("evidence", "")

                if evidence:
                    value += (
                        "\n**Evidence:** "
                        + truncate_text(evidence, 200)
                    )

            embed.add_field(
                name=truncate_text(
                    f"#{item['id']} {item['objective']}",
                    256,
                ),
                value=truncate_text(value, 1024),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @objective_group.command(
        name="history",
        description="View previous assessments for an objective.",
    )
    @app_commands.describe(
        objective_id="The ID of the objective.",
    )
    async def objective_history(
        interaction: discord.Interaction,
        objective_id: int,
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        objective = get_objective(
            objective_id=objective_id,
            guild_id=guild.id,
        )

        if objective is None:
            await interaction.response.send_message(
                "That objective does not exist in this server.",
                ephemeral=True,
            )
            return

        assessments = get_objective_assessments(
            objective_id=objective_id,
            guild_id=guild.id,
            limit=5,
        )

        if not assessments:
            await interaction.response.send_message(
                f"Objective `#{objective_id}` has no recorded "
                "assessment history yet.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=truncate_text(
                f"Assessment History: #{objective_id}",
                256,
            ),
            description=truncate_text(
                objective["objective"],
                4000,
            ),
            color=discord.Color.blurple(),
        )

        for index, assessment in enumerate(assessments, start=1):
            value = (
                f"**Status:** `{assessment['status']}`\n"
                f"**Recorded:** "
                f"{format_timestamp(assessment['created_at'])}\n\n"
                f"{truncate_text(assessment['assessment'], 450)}"
            )

            evidence = assessment.get("evidence", "")

            if evidence:
                value += (
                    "\n\n**Evidence**\n"
                    + truncate_text(evidence, 350)
                )

            embed.add_field(
                name=f"Assessment {index}",
                value=truncate_text(value, 1024),
                inline=False,
            )

        embed.set_footer(
            text="Showing the 5 most recent assessments at most."
        )

        await interaction.response.send_message(embed=embed)

    @objective_group.command(
        name="remove",
        description="Remove a server objective.",
    )
    @app_commands.describe(
        objective_id="The ID of the objective to remove.",
    )
    async def objective_remove(
        interaction: discord.Interaction,
        objective_id: int,
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        objective = get_objective(
            objective_id=objective_id,
            guild_id=guild.id,
        )

        if objective is None:
            await interaction.response.send_message(
                "That objective does not exist.",
                ephemeral=True,
            )
            return

        deleted = delete_objective(
            objective_id=objective_id,
            guild_id=guild.id,
        )

        if not deleted:
            await interaction.response.send_message(
                "I couldn't remove that objective.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Removed objective `#{objective_id}`."
        )

    @objective_group.command(
        name="pause",
        description="Pause a server objective.",
    )
    @app_commands.describe(
        objective_id="The ID of the objective to pause.",
    )
    async def objective_pause(
        interaction: discord.Interaction,
        objective_id: int,
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        objective = get_objective(
            objective_id=objective_id,
            guild_id=guild.id,
        )

        if objective is None:
            await interaction.response.send_message(
                "That objective does not exist.",
                ephemeral=True,
            )
            return

        updated = update_objective(
            objective_id=objective_id,
            guild_id=guild.id,
            status="paused",
        )

        if not updated:
            await interaction.response.send_message(
                "I couldn't pause that objective.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Paused objective `#{objective_id}`."
        )

    @objective_group.command(
        name="resume",
        description="Resume a paused server objective.",
    )
    @app_commands.describe(
        objective_id="The ID of the objective to resume.",
    )
    async def objective_resume(
        interaction: discord.Interaction,
        objective_id: int,
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        objective = get_objective(
            objective_id=objective_id,
            guild_id=guild.id,
        )

        if objective is None:
            await interaction.response.send_message(
                "That objective does not exist.",
                ephemeral=True,
            )
            return

        updated = update_objective(
            objective_id=objective_id,
            guild_id=guild.id,
            status="active",
        )

        if not updated:
            await interaction.response.send_message(
                "I couldn't resume that objective.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Resumed objective `#{objective_id}`."
        )

    bot.tree.add_command(objective_group)