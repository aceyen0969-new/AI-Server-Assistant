import discord


async def setup(bot):

    @bot.tree.command(
        name="serverstats",
        description="Show detailed statistics about this server."
    )
    async def serverstats(interaction: discord.Interaction):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server."
            )

            return


        # =================================================
        # CHANNEL COUNTS
        # =================================================

        text_channels = len(guild.text_channels)

        voice_channels = len(guild.voice_channels)

        categories = len(guild.categories)

        total_channels = len(guild.channels)


        # =================================================
        # MEMBER COUNTS
        # =================================================

        total_members = guild.member_count or 0


        bot_count = sum(
            1
            for member in guild.members
            if member.bot
        )


        human_count = total_members - bot_count


        online_members = sum(
            1
            for member in guild.members
            if member.status != discord.Status.offline
        )


        # =================================================
        # ROLE COUNT
        # =================================================

        role_count = len(guild.roles) - 1

        if role_count < 0:
            role_count = 0


        # =================================================
        # EMBED
        # =================================================

        embed = discord.Embed(
            title=f"📊 {guild.name} Server Statistics",
            description="Detailed overview of your Discord server.",
            color=discord.Color.blurple()
        )


        embed.add_field(
            name="👥 Members",
            value=(
                f"Total: **{total_members:,}**\n"
                f"Humans: **{human_count:,}**\n"
                f"Bots: **{bot_count:,}**\n"
                f"Online: **{online_members:,}**"
            ),
            inline=True
        )


        embed.add_field(
            name="💬 Channels",
            value=(
                f"Total: **{total_channels:,}**\n"
                f"Text: **{text_channels:,}**\n"
                f"Voice: **{voice_channels:,}**\n"
                f"Categories: **{categories:,}**"
            ),
            inline=True
        )


        embed.add_field(
            name="🏗️ Structure",
            value=(
                f"Roles: **{role_count:,}**\n"
                f"Server ID: `{guild.id}`"
            ),
            inline=True
        )


        if guild.owner:

            embed.add_field(
                name="👑 Owner",
                value=guild.owner.mention,
                inline=False
            )


        if guild.icon:

            embed.set_thumbnail(
                url=guild.icon.url
            )


        embed.set_footer(
            text="AI Server Assistant • Server Analytics"
        )


        await interaction.response.send_message(
            embed=embed
        )
