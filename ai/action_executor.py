import discord


async def execute_action(
    guild: discord.Guild,
    action: dict,
) -> bool:
    """
    Execute one validated Discord action.

    Returns True if the action succeeds.
    Returns False if the action fails.
    """

    if not isinstance(action, dict):
        return False

    action_type = action.get("action")

    if action_type == "move_channel":
        return await move_channel(
            guild,
            action,
        )

    return False


async def move_channel(
    guild: discord.Guild,
    action: dict,
) -> bool:
    """Move a channel into a category."""

    channel_id = action.get("channel_id")
    category_id = action.get("category_id")

    if not isinstance(channel_id, int):
        return False

    if not isinstance(category_id, int):
        return False

    channel = guild.get_channel(channel_id)
    category = guild.get_channel(category_id)

    if channel is None:
        return False

    if category is None:
        return False

    if not isinstance(
        category,
        discord.CategoryChannel,
    ):
        return False

    if not isinstance(
        channel,
        (
            discord.TextChannel,
            discord.VoiceChannel,
        ),
    ):
        return False

    try:
        await channel.edit(
            category=category,
            reason="AI Server Assistant action",
        )

    except discord.Forbidden:
        return False

    except discord.HTTPException:
        return False

    return True