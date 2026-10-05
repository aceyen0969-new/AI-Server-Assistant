import discord


async def setup(bot):

    @bot.tree.command(
        name="ping",
        description="Check if the bot is online."
    )
    async def ping(interaction: discord.Interaction):

        latency = round(bot.latency * 1000)

        await interaction.response.send_message(
            f"🏓 Pong! `{latency}ms`"
        )