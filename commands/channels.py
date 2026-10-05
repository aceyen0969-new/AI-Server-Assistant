import discord


async def setup(bot):

    @bot.tree.command(
        name="channels",
        description="Analyze the server's channel organization."
    )
    async def channels(interaction: discord.Interaction):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server."
            )

            return


        # =================================================
        # CREATE CHANNEL STRUCTURE
        # =================================================

        categories = guild.categories

        category_data = []

        uncategorized = []


        # =================================================
        # CHECK CATEGORIES
        # =================================================

        for category in categories:

            text_channels = []

            voice_channels = []


            for channel in category.channels:

                if isinstance(
                    channel,
                    discord.TextChannel
                ):

                    text_channels.append(
                        f"#{channel.name}"
                    )


                elif isinstance(
                    channel,
                    discord.VoiceChannel
                ):

                    voice_channels.append(
                        f"🔊 {channel.name}"
                    )


            category_data.append(
                (
                    category.name,
                    text_channels,
                    voice_channels
                )
            )


        # =================================================
        # FIND UNCATEGORIZED CHANNELS
        # =================================================

        for channel in guild.channels:

            if channel.category is not None:
                continue


            if isinstance(
                channel,
                discord.TextChannel
            ):

                uncategorized.append(
                    f"#{channel.name}"
                )


            elif isinstance(
                channel,
                discord.VoiceChannel
            ):

                uncategorized.append(
                    f"🔊 {channel.name}"
                )


        # =================================================
        # CREATE EMBED
        # =================================================

        embed = discord.Embed(
            title=f"📋 {guild.name} Channel Structure",
            description=(
                "Current organization of your server channels."
            ),
            color=discord.Color.blurple()
        )


        # =================================================
        # CATEGORY FIELDS
        # =================================================

        for category_name, text_channels, voice_channels in category_data:

            channel_list = []

            channel_list.extend(text_channels)

            channel_list.extend(voice_channels)


            if not channel_list:

                channel_list.append(
                    "No channels"
                )


            channel_text = "\n".join(
                channel_list
            )


            # Discord embed field limit
            if len(channel_text) > 1000:

                channel_text = (
                    channel_text[:997]
                    + "..."
                )


            embed.add_field(
                name=f"📁 {category_name}",
                value=channel_text,
                inline=False
            )


        # =================================================
        # UNCATEGORIZED CHANNELS
        # =================================================

        if uncategorized:

            uncategorized_text = "\n".join(
                uncategorized
            )


            if len(uncategorized_text) > 1000:

                uncategorized_text = (
                    uncategorized_text[:997]
                    + "..."
                )


            embed.add_field(
                name="⚠️ Uncategorized",
                value=uncategorized_text,
                inline=False
            )


        else:

            embed.add_field(
                name="✅ Uncategorized",
                value=(
                    "All channels are currently "
                    "inside categories."
                ),
                inline=False
            )


        # =================================================
        # SUMMARY
        # =================================================

        embed.add_field(
            name="📊 Summary",
            value=(
                f"Categories: **{len(categories)}**\n"
                f"Text channels: **{len(guild.text_channels)}**\n"
                f"Voice channels: **{len(guild.voice_channels)}**"
            ),
            inline=False
        )


        embed.set_footer(
            text="AI Server Assistant • Channel Analyzer"
        )


        await interaction.response.send_message(
            embed=embed
        )
