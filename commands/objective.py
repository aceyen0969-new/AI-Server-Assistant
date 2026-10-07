import discord
from discord import app_commands

from analytics.database import (
    create_objective,
    get_objectives,
    get_objective,
    update_objective,
    delete_objective,
)


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
            app_commands.Choice(
                name="Low",
                value="low",
            ),
            app_commands.Choice(
                name="Normal",
                value="normal",
            ),
            app_commands.Choice(
                name="High",
                value="high",
            ),
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

        if not objective.strip():
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
            objective=objective.strip(),
            description=description.strip(),
            priority=priority.value,
        )

        embed = discord.Embed(
            title="Objective Added",
            description=(
                f"**Objective:** {objective.strip()}\n"
                f"**Priority:** `{priority.value}`\n"
                f"**Status:** `active`"
            ),
            color=discord.Color.green(),
        )

        if description.strip():
            embed.add_field(
                name="Description",
                value=description.strip(),
                inline=False,
            )

        embed.set_footer(
            text=f"Objective ID: {objective_id}"
        )

        await interaction.response.send_message(
            embed=embed,
        )

    @objective_group.command(
        name="list",
        description="List the server's objectives.",
    )
    @app_commands.describe(
        status="Filter objectives by status.",
    )
    @app_commands.choices(
        status=[
            app_commands.Choice(
                name="Active",
                value="active",
            ),
            app_commands.Choice(
                name="Paused",
                value="paused",
            ),
            app_commands.Choice(
                name="Completed",
                value="completed",
            ),
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

            objective_id = item["id"]
            objective = item["objective"]
            priority = item["priority"]
            item_status = item["status"]
            description = item["description"] or ""

            value = (
                f"**Priority:** `{priority}`\n"
                f"**Status:** `{item_status}`"
            )

            if description:
                value += f"\n**Details:** {description}"

            embed.add_field(
                name=f"#{objective_id} {objective}",
                value=value,
                inline=False,
            )

        await interaction.response.send_message(
            embed=embed,
        )

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
            f"Removed objective `#{objective_id}`.",
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
            f"Paused objective `#{objective_id}`.",
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
            f"Resumed objective `#{objective_id}`.",
        )

    bot.tree.add_command(
        objective_group
    )