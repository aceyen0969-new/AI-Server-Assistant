from datetime import datetime, timezone

import discord

from analytics.database import record_message


async def handle_message(
    message: discord.Message,
):
    """Record useful message activity."""

    if message.guild is None:
        return

    if message.author.bot:
        return

    created_at = message.created_at

    if created_at.tzinfo is None:
        created_at = created_at.replace(
            tzinfo=timezone.utc
        )

    record_message(
        guild_id=message.guild.id,
        channel_id=message.channel.id,
        user_id=message.author.id,
        created_at=created_at.isoformat(),
    )