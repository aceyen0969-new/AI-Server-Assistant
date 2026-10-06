import discord


async def execute_action(
    guild: discord.Guild,
    action: dict,
    reason: str = "AI Server Assistant action",
) -> bool:
    if not isinstance(action, dict):
        return False

    action_type = action.get("action")

    if action_type == "move_channel":
        return await move_channel(
            guild,
            action,
            reason,
        )

    if action_type == "rename_channel":
        return await rename_channel(
            guild,
            action,
            reason,
        )

    return False


async def move_channel(
    guild: discord.Guild,
    action: dict,
    reason: str,
) -> bool:
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

    if not isinstance(category, discord.CategoryChannel):
        return False

    if not isinstance(
        channel,
        (
            discord.TextChannel,
            discord.VoiceChannel,
        ),
    ):
        return False

    if channel.category_id == category.id:
        return False

    try:
        await channel.edit(
            category=category,
            reason=reason,
        )
    except discord.Forbidden:
        return False
    except discord.HTTPException:
        return False

    return True


async def rename_channel(
    guild: discord.Guild,
    action: dict,
    reason: str,
) -> bool:
    channel_id = action.get("channel_id")
    new_name = action.get("new_name")

    if not isinstance(channel_id, int):
        return False

    if not isinstance(new_name, str):
        return False

    new_name = new_name.strip()

    if not new_name:
        return False

    if len(new_name) > 100:
        return False

    channel = guild.get_channel(channel_id)

    if channel is None:
        return False

    if not isinstance(
        channel,
        (
            discord.TextChannel,
            discord.VoiceChannel,
        ),
    ):
        return False

    if channel.name == new_name:
        return False

    try:
        await channel.edit(
            name=new_name,
            reason=reason,
        )
    except discord.Forbidden:
        return False
    except discord.HTTPException:
        return False

    return True