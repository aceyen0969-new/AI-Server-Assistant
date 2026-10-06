
import discord

from ai.health import (
    get_status,
    get_ai_status
)


async def setup(bot):

    @bot.tree.command(
        name="ai-status",
        description="Check the health of all AI providers."
    )
    async def ai_status(
        interaction: discord.Interaction
    ):

        statuses = get_status()
        overall = get_ai_status()

        lines = []


        # =================================================
        # PROVIDER STATUS
        # =================================================

        for provider_name, info in statuses.items():

            status = info["status"]


            if status == "online":

                icon = "🟢"
                label = "Online"


            elif status == "offline":

                icon = "🔴"
                label = "Unavailable"


            else:

                icon = "⚪"
                label = "Not tested"


            lines.append(
                f"{icon} **{provider_name}**\n"
                f"   {label}"
            )


        # =================================================
        # OVERALL STATUS
        # =================================================

        if overall == "online":

            overall_text = (
                "🟢 **AI ONLINE**\n"
                "At least one AI provider is available."
            )

            color = discord.Color.green()


        else:

            # Unknown providers are not considered online
            # until they have actually been tested.

            overall_text = (
                "🔴 **AI OFFLINE**\n"
                "No AI provider has successfully responded yet."
            )

            color = discord.Color.red()


        # =================================================
        # EMBED
        # =================================================

        embed = discord.Embed(
            title="🧠 AI Provider Status",
            description="\n\n".join(lines),
            color=color
        )


        embed.add_field(
            name="Overall Status",
            value=overall_text,
            inline=False
        )


        embed.set_footer(
            text="AI Server Assistant"
        )


        await interaction.response.send_message(
            embed=embed
        )
