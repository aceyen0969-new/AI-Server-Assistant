
import sqlite3

import discord
from discord import app_commands
from discord.ext import commands

from analytics.database import DATABASE_PATH
from onboarding import get_server_config, save_server_config


def initialize_access_database():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_access_settings (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_access_roles (
                guild_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                added_by INTEGER,
                PRIMARY KEY (guild_id, role_id)
            )
            """
        )


def get_authorized_roles(guild_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT role_id
            FROM analytics_access_roles
            WHERE guild_id = ?
            ORDER BY role_id
            """,
            (guild_id,),
        ).fetchall()

    return [row[0] for row in rows]


def is_access_setup(guild_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            """
            SELECT enabled
            FROM analytics_access_settings
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()

    return bool(row and row[0])


def set_access_setup(guild_id, enabled):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO analytics_access_settings (guild_id, enabled)
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET enabled = excluded.enabled
            """,
            (guild_id, int(enabled)),
        )


def save_authorized_role(guild_id, role_id, added_by):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO analytics_access_roles (
                guild_id,
                role_id,
                added_by
            )
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, role_id)
            DO UPDATE SET added_by = excluded.added_by
            """,
            (guild_id, role_id, added_by),
        )


def delete_authorized_role(guild_id, role_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            DELETE FROM analytics_access_roles
            WHERE guild_id = ? AND role_id = ?
            """,
            (guild_id, role_id),
        )


def get_analytics_channel(guild):
    config = get_server_config(guild.id) or {}
    channel_id = config.get("analytics_channel_id")

    channel = guild.get_channel(channel_id) if channel_id else None

    if isinstance(channel, discord.TextChannel):
        return channel

    for name in ("quasar-reports", "analytics"):
        channel = discord.utils.get(guild.text_channels, name=name)

        if channel is not None:
            save_server_config(
                guild.id,
                analytics_channel_id=channel.id,
            )
            return channel

    return None


class AnalyticsAccess(commands.Cog):
    analytics_access = app_commands.Group(
        name="analytics-access",
        description="Manage access to Quasar analytics reports.",
    )

    def __init__(self, bot):
        self.bot = bot
        initialize_access_database()

    async def interaction_check(self, interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return False

        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(
                "Only the server owner can manage analytics access.",
                ephemeral=True,
            )
            return False

        return True

    def bot_can_manage_channel(self, guild, channel):
        bot_member = guild.me

        if bot_member is None:
            return False

        permissions = channel.permissions_for(bot_member)

        return (
            permissions.view_channel
            and permissions.manage_roles
        )

    @analytics_access.command(
        name="setup",
        description="Make the analytics channel private.",
    )
    async def setup_access(
        self,
        interaction: discord.Interaction,
    ):
        if not await self.interaction_check(interaction):
            return

        guild = interaction.guild
        channel = get_analytics_channel(guild)

        if channel is None:
            await interaction.response.send_message(
                "I couldn't find the saved analytics channel. "
                "Make sure #quasar-reports exists.",
                ephemeral=True,
            )
            return

        if not self.bot_can_manage_channel(guild, channel):
            await interaction.response.send_message(
                "I need View Channel and Manage Roles permissions "
                "for the analytics channel so I can configure its "
                "permission overwrites.",
                ephemeral=True,
            )
            return

        try:
            overwrites = channel.overwrites

            everyone_overwrite = overwrites.get(
                guild.default_role,
                discord.PermissionOverwrite(),
            )
            everyone_overwrite.view_channel = False
            everyone_overwrite.send_messages = False
            everyone_overwrite.read_message_history = False

            overwrites[guild.default_role] = everyone_overwrite

            bot_member = guild.me
            bot_overwrite = overwrites.get(
                bot_member,
                discord.PermissionOverwrite(),
            )
            bot_overwrite.view_channel = True
            bot_overwrite.send_messages = True
            bot_overwrite.read_message_history = True
            bot_overwrite.embed_links = True

            overwrites[bot_member] = bot_overwrite

            for role_id in get_authorized_roles(guild.id):
                role = guild.get_role(role_id)

                if role is None:
                    continue

                role_overwrite = overwrites.get(
                    role,
                    discord.PermissionOverwrite(),
                )
                role_overwrite.view_channel = True
                role_overwrite.read_message_history = True

                overwrites[role] = role_overwrite

            await channel.edit(
                overwrites=overwrites,
                reason="Server owner configured Quasar analytics access",
            )

            set_access_setup(guild.id, True)

            await interaction.response.send_message(
                f"🔒 {channel.mention} is now private. "
                "The server owner and Quasar retain access. "
                "Use `/analytics-access add` to authorize roles.",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Discord denied permission to update this channel. "
                "Check Quasar's role position and channel permissions.",
                ephemeral=True,
            )

        except discord.HTTPException as exc:
            print(
                f"ANALYTICS ACCESS: Setup failed for guild "
                f"{guild.id}: {exc!r}",
                flush=True,
            )

            await interaction.response.send_message(
                "I couldn't configure the channel. Check the bot's "
                "permissions and try again.",
                ephemeral=True,
            )

    @analytics_access.command(
        name="add",
        description="Allow a role to view analytics reports.",
    )
    @app_commands.describe(role="The server role to authorize")
    async def add_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ):
        if not await self.interaction_check(interaction):
            return

        guild = interaction.guild

        if role.is_default():
            await interaction.response.send_message(
                "You cannot authorize @everyone. Choose a specific role.",
                ephemeral=True,
            )
            return

        if role.is_bot_managed() or role.is_integration():
            await interaction.response.send_message(
                "Choose a regular server role rather than a "
                "managed integration role.",
                ephemeral=True,
            )
            return

        if not is_access_setup(guild.id):
            await interaction.response.send_message(
                "Run `/analytics-access setup` first.",
                ephemeral=True,
            )
            return

        channel = get_analytics_channel(guild)

        if channel is None:
            await interaction.response.send_message(
                "I couldn't find the analytics channel.",
                ephemeral=True,
            )
            return

        if not self.bot_can_manage_channel(guild, channel):
            await interaction.response.send_message(
                "I need View Channel and Manage Roles permissions "
                "to update analytics access.",
                ephemeral=True,
            )
            return

        try:
            await channel.set_permissions(
                role,
                overwrite=discord.PermissionOverwrite(
                    view_channel=True,
                    read_message_history=True,
                ),
                reason="Server owner authorized analytics access",
            )

            save_authorized_role(
                guild.id,
                role.id,
                interaction.user.id,
            )

            await interaction.response.send_message(
                f"✅ {role.mention} can now view {channel.mention}.",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Discord denied the permission change. Check Quasar's "
                "role hierarchy and channel permissions.",
                ephemeral=True,
            )

        except discord.HTTPException as exc:
            print(
                f"ANALYTICS ACCESS: Adding role failed: {exc!r}",
                flush=True,
            )

            await interaction.response.send_message(
                "I couldn't update that role's permissions.",
                ephemeral=True,
            )

    @analytics_access.command(
        name="remove",
        description="Revoke a role's analytics access.",
    )
    @app_commands.describe(role="The server role to remove")
    async def remove_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
    ):
        if not await self.interaction_check(interaction):
            return

        guild = interaction.guild

        if role.is_default():
            await interaction.response.send_message(
                "The @everyone role cannot be removed from this list.",
                ephemeral=True,
            )
            return

        if not is_access_setup(guild.id):
            await interaction.response.send_message(
                "Run `/analytics-access setup` first.",
                ephemeral=True,
            )
            return

        channel = get_analytics_channel(guild)

        if channel is None:
            await interaction.response.send_message(
                "I couldn't find the analytics channel.",
                ephemeral=True,
            )
            return

        if not self.bot_can_manage_channel(guild, channel):
            await interaction.response.send_message(
                "I need View Channel and Manage Roles permissions "
                "to update analytics access.",
                ephemeral=True,
            )
            return

        if role.id not in get_authorized_roles(guild.id):
            await interaction.response.send_message(
                f"{role.mention} isn't in Quasar's authorized role list.",
                ephemeral=True,
            )
            return

        try:
            await channel.set_permissions(
                role,
                overwrite=None,
                reason="Server owner revoked analytics access",
            )

            delete_authorized_role(guild.id, role.id)

            await interaction.response.send_message(
                f"🔒 Access for {role.mention} has been revoked.",
                ephemeral=True,
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Discord denied the permission change. Check Quasar's "
                "role hierarchy and channel permissions.",
                ephemeral=True,
            )

        except discord.HTTPException as exc:
            print(
                f"ANALYTICS ACCESS: Removing role failed: {exc!r}",
                flush=True,
            )

            await interaction.response.send_message(
                "I couldn't update that role's permissions.",
                ephemeral=True,
            )

    @analytics_access.command(
        name="list",
        description="List roles authorized to view analytics.",
    )
    async def list_roles(
        self,
        interaction: discord.Interaction,
    ):
        if not await self.interaction_check(interaction):
            return

        guild = interaction.guild

        if not is_access_setup(guild.id):
            await interaction.response.send_message(
                "Analytics access hasn't been configured yet. "
                "Run `/analytics-access setup` first.",
                ephemeral=True,
            )
            return

        role_ids = get_authorized_roles(guild.id)
        role_names = []

        for role_id in role_ids:
            role = guild.get_role(role_id)

            if role is not None:
                role_names.append(role.mention)
            else:
                role_names.append(f"Deleted role (`{role_id}`)")

        channel = get_analytics_channel(guild)
        channel_text = channel.mention if channel else "Not found"

        if role_names:
            roles_text = "\n".join(role_names)
        else:
            roles_text = "No additional roles have been authorized."

        embed = discord.Embed(
            title="🔐 Analytics Access",
            description=(
                f"**Channel:** {channel_text}\n"
                f"**Authorized roles:**\n{roles_text}\n\n"
                "The server owner retains access. Discord administrators "
                "can also bypass channel restrictions."
            ),
            color=discord.Color.blurple(),
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    async def cog_load(self):
        initialize_access_database()


async def setup(bot: commands.Bot):
    await bot.add_cog(AnalyticsAccess(bot))
