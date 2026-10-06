import discord


async def execute_action(
    guild: discord.Guild,
    action: dict,
    reason: str | None = None,
) -> bool:
    """Execute a validated Discord action."""

    action_type = action.get(
        "action"
    )

    if action_type == "move_channel":

        channel_id = action.get(
            "channel_id"
        )

        category_id = action.get(
            "category_id"
        )

        if not isinstance(
            channel_id,
            int,
        ):

            return False

        if not isinstance(
            category_id,
            int,
        ):

            return False

        channel = guild.get_channel(
            channel_id
        )

        category = guild.get_channel(
            category_id
        )

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
                discord.StageChannel,
                discord.ForumChannel,
            ),
        ):

            return False

        try:

            await channel.edit(
                category=category,
                reason=reason,
            )

            return True

        except discord.HTTPException:

            return False

    if action_type == "rename_channel":

        channel_id = action.get(
            "channel_id"
        )

        new_name = action.get(
            "new_name"
        )

        if not isinstance(
            channel_id,
            int,
        ):

            return False

        if not isinstance(
            new_name,
            str,
        ):

            return False

        new_name = new_name.strip()

        if not new_name:

            return False

        if len(new_name) > 100:

            return False

        channel = guild.get_channel(
            channel_id
        )

        if channel is None:

            return False

        if not isinstance(
            channel,
            (
                discord.TextChannel,
                discord.VoiceChannel,
                discord.StageChannel,
                discord.ForumChannel,
            ),
        ):

            return False

        try:

            await channel.edit(
                name=new_name,
                reason=reason,
            )

            return True

        except discord.HTTPException:

            return False

    if action_type == "create_channel":

        name = action.get(
            "name"
        )

        channel_type = action.get(
            "channel_type"
        )

        if not isinstance(
            name,
            str,
        ):

            return False

        name = name.strip()

        if not name:

            return False

        if len(name) > 100:

            return False

        if channel_type not in (
            "text",
            "voice",
        ):

            return False

        existing_channel = discord.utils.get(
            guild.channels,
            name=name,
        )

        if existing_channel is not None:

            return False

        try:

            if channel_type == "text":

                await guild.create_text_channel(
                    name=name,
                    reason=reason,
                )

            elif channel_type == "voice":

                await guild.create_voice_channel(
                    name=name,
                    reason=reason,
                )

            return True

        except discord.HTTPException:

            return False

    return False