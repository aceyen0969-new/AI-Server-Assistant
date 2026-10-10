import asyncio
import sqlite3

import discord

from analytics.database import DATABASE_PATH


ASSISTANT_CHANNEL_NAME = "ai-assistant"
ANALYTICS_CHANNEL_NAME = "analytics"

_setup_locks = {}


def initialize_onboarding_database():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS server_channel_config (
                guild_id INTEGER PRIMARY KEY,
                assistant_channel_id INTEGER,
                analytics_channel_id INTEGER,
                setup_completed INTEGER NOT NULL DEFAULT 0,
                assistant_welcome_sent INTEGER NOT NULL DEFAULT 0,
                analytics_welcome_sent INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def get_server_config(guild_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT *
            FROM server_channel_config
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchone()

        return dict(row) if row else None


def save_server_config(guild_id, **values):
    allowed_fields = {
        "assistant_channel_id",
        "analytics_channel_id",
        "setup_completed",
        "assistant_welcome_sent",
        "analytics_welcome_sent",
    }

    if not values or not set(values).issubset(allowed_fields):
        raise ValueError("Invalid server configuration fields.")

    assignments = ", ".join(
        f"{field} = ?" for field in values
    )

    parameters = list(values.values())
    parameters.append(guild_id)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            f"""
            INSERT INTO server_channel_config (guild_id)
            VALUES (?)
            ON CONFLICT(guild_id) DO NOTHING
            """,
            (guild_id,),
        )

        connection.execute(
            f"""
            UPDATE server_channel_config
            SET {assignments}
            WHERE guild_id = ?
            """,
            parameters,
        )


def find_channel_by_id(guild, channel_id):
    if not channel_id:
        return None

    channel = guild.get_channel(channel_id)

    if isinstance(channel, discord.TextChannel):
        return channel

    return None


def find_channel_by_name(guild, name):
    return discord.utils.get(
        guild.text_channels,
        name=name,
    )


async def get_or_create_channel(guild, channel_id, channel_name):
    channel = find_channel_by_id(guild, channel_id)

    if channel is not None:
        return channel, False

    channel = find_channel_by_name(guild, channel_name)

    if channel is not None:
        return channel, False

    bot_member = guild.me

    if bot_member is None:
        return None, False

    if not bot_member.guild_permissions.manage_channels:
        print(
            "ONBOARDING: Cannot create channel "
            f"#{channel_name} in {guild.name}. "
            "Quasar needs Manage Channels permission.",
            flush=True,
        )
        return None, False

    try:
        channel = await guild.create_text_channel(
            channel_name,
            reason="Quasar automatic server setup",
        )

        print(
            "ONBOARDING: Created "
            f"#{channel.name} in {guild.name} "
            f"(guild_id={guild.id}, channel_id={channel.id})",
            flush=True,
        )

        return channel, True

    except discord.Forbidden:
        print(
            "ONBOARDING: Discord denied permission to create "
            f"#{channel_name} in {guild.name}.",
            flush=True,
        )

    except discord.HTTPException as exc:
        print(
            "ONBOARDING: Failed to create "
            f"#{channel_name} in {guild.name}: {exc!r}",
            flush=True,
        )

    return None, False


async def send_setup_messages(
    guild,
    assistant_channel,
    analytics_channel,
    config,
    assistant_created,
    analytics_created,
):
    if assistant_created and not config["assistant_welcome_sent"]:
        try:
            await assistant_channel.send(
                f"Hello, {guild.name}! I'm Quasar. 🚀\n\n"
                "This is your AI assistant channel. You can chat "
                "with me here and ask for help with your server.\n\n"
                "Your administrators can rename this channel "
                "whenever they like. I'll remember it."
            )

            save_server_config(
                guild.id,
                assistant_welcome_sent=1,
            )

        except discord.HTTPException as exc:
            print(
                "ONBOARDING: Could not send assistant welcome "
                f"in {guild.name}: {exc!r}",
                flush=True,
            )

    if analytics_created and not config["analytics_welcome_sent"]:
        try:
            await analytics_channel.send(
                "📊 **Quasar Analytics is ready!**\n\n"
                "Automated server analytics reports will be "
                "posted here when the analytics scheduler runs.\n\n"
                "Administrators can rename this channel. "
                "Quasar will remember its channel ID."
            )

            save_server_config(
                guild.id,
                analytics_welcome_sent=1,
            )

        except discord.HTTPException as exc:
            print(
                "ONBOARDING: Could not send analytics welcome "
                f"in {guild.name}: {exc!r}",
                flush=True,
            )


async def ensure_server_setup(guild):
    lock = _setup_locks.setdefault(
        guild.id,
        asyncio.Lock(),
    )

    async with lock:
        config = get_server_config(guild.id) or {
            "guild_id": guild.id,
            "assistant_channel_id": None,
            "analytics_channel_id": None,
            "setup_completed": 0,
            "assistant_welcome_sent": 0,
            "analytics_welcome_sent": 0,
        }

        assistant_channel, assistant_created = (
            await get_or_create_channel(
                guild,
                config["assistant_channel_id"],
                ASSISTANT_CHANNEL_NAME,
            )
        )

        analytics_channel, analytics_created = (
            await get_or_create_channel(
                guild,
                config["analytics_channel_id"],
                ANALYTICS_CHANNEL_NAME,
            )
        )

        updates = {}

        if assistant_channel is not None:
            updates["assistant_channel_id"] = assistant_channel.id

        if analytics_channel is not None:
            updates["analytics_channel_id"] = analytics_channel.id

        setup_completed = (
            assistant_channel is not None
            and analytics_channel is not None
        )

        updates["setup_completed"] = int(setup_completed)

        save_server_config(guild.id, **updates)

        if assistant_channel is not None and analytics_channel is not None:
            refreshed_config = get_server_config(guild.id)

            await send_setup_messages(
                guild,
                assistant_channel,
                analytics_channel,
                refreshed_config,
                assistant_created,
                analytics_created,
            )

            print(
                "ONBOARDING: Setup complete "
                f"for {guild.name} (guild_id={guild.id}). "
                f"Assistant=#{assistant_channel.name}, "
                f"Analytics=#{analytics_channel.name}",
                flush=True,
            )
        else:
            print(
                "ONBOARDING: Setup incomplete for "
                f"{guild.name}. Check Manage Channels permission "
                "and the Deploy Logs.",
                flush=True,
            )


async def onboarding_on_guild_join(guild):
    print(
        f"ONBOARDING: Quasar joined {guild.name} "
        f"(guild_id={guild.id}).",
        flush=True,
    )

    await ensure_server_setup(guild)


async def onboarding_on_ready(bot):
    for guild in bot.guilds:
        try:
            await ensure_server_setup(guild)

        except Exception as exc:
            print(
                "ONBOARDING ERROR: "
                f"guild={guild.name}, "
                f"guild_id={guild.id}, "
                f"error={exc!r}",
                flush=True,
            )


def register_onboarding(bot):
    initialize_onboarding_database()

    bot.add_listener(
        onboarding_on_guild_join,
        "on_guild_join",
    )

    async def on_ready():
        await onboarding_on_ready(bot)

    bot.add_listener(on_ready, "on_ready")

    print(
        "ONBOARDING: Automatic server setup registered.",
        flush=True,
    )