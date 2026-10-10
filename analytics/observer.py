
from datetime import timezone

import discord

from analytics.database import (
    DATABASE_PATH,
    get_message_count,
    record_message,
)


async def handle_message(message: discord.Message):
    if message.guild is None:
        return

    if message.author.bot:
        return

    created_at = message.created_at

    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    try:
        record_message(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            user_id=message.author.id,
            created_at=created_at.isoformat(),
        )

        total_messages = get_message_count(message.guild.id)

        print(
            "ANALYTICS DATABASE WRITE DEBUG: "
            f"guild_id={message.guild.id}, "
            f"channel_id={message.channel.id}, "
            f"user_id={message.author.id}, "
            f"database={DATABASE_PATH}, "
            f"total_messages_after_insert={total_messages}",
            flush=True,
        )

    except Exception as exc:
        print(
            "ANALYTICS DATABASE WRITE ERROR: "
            f"guild_id={message.guild.id}, "
            f"channel_id={message.channel.id}, "
            f"error={exc!r}",
            flush=True,
        )
        raise
