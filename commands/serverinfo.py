import discord


async def setup(bot):

    @bot.tree.command(
        name="serverinfo",
        description="Show basic information about this Discord server."
    )
    async def serverinfo(interaction: discord.Interaction):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "This command can only be used inside a server."
            )

            return


        embed = discord.Embed(
            title=f"📊 {guild.name}",
            description="Server information",
            color=discord.Color.blurple()
        )


        embed.add_field(
            name="👥 Members",
            value=f"{guild.member_count:,}",
            inline=True
        )


        embed.add_field(
            name="💬 Channels",
            value=str(len(guild.channels)),
            inline=True
        )


        embed.add_field(
            name="🎭 Roles",
            value=str(len(guild.roles)),
            inline=True
        )


        embed.add_field(
            name="🆔 Server ID",
            value=str(guild.id),
            inline=False
        )


        if guild.icon:

            embed.set_thumbnail(
                url=guild.icon.url
            )


        await interaction.response.send_message(
            embed=embed
        )
