import asyncio

import discord
from discord import app_commands


async def setup(bot):

    @bot.tree.command(
        name="cleanup",
        description="Clean up messages in the current channel."
    )
    @app_commands.describe(
        amount="Number of recent messages to delete.",
        delete_all="Delete all accessible messages in this channel."
    )
    async def cleanup(
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100] | None = None,
        delete_all: bool = False
    ):

        # =============================================
        # SERVER CHECK
        # =============================================

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ This command can only be used inside a server.",
                ephemeral=True
            )

            return


        # =============================================
        # PERMISSION CHECK
        # =============================================

        if not interaction.user.guild_permissions.manage_messages:

            await interaction.response.send_message(
                "❌ You need the **Manage Messages** permission "
                "to use this command.",
                ephemeral=True
            )

            return


        # =============================================
        # REQUIRE AN OPTION
        # =============================================

        if amount is None and not delete_all:

            await interaction.response.send_message(
                "❌ Specify an amount or set "
                "`delete_all` to `True`.",
                ephemeral=True
            )

            return


        # =============================================
        # PREVENT BOTH OPTIONS
        # =============================================

        if amount is not None and delete_all:

            await interaction.response.send_message(
                "❌ Choose either an amount OR "
                "`delete_all`, not both.",
                ephemeral=True
            )

            return


        # =============================================
        # DELETE ALL CONFIRMATION
        # =============================================

        if delete_all:

            embed = discord.Embed(
                title="🚨 DELETE ALL MESSAGES?",
                description=(
                    f"You are about to delete **ALL accessible "
                    f"messages** in {interaction.channel.mention}.\n\n"
                    "⚠️ **This action cannot be undone.**\n"
                    "⚠️ Old messages may take longer to delete.\n\n"
                    "Only confirm if you are absolutely sure."
                ),
                color=discord.Color.red()
            )

            embed.set_footer(
                text="This confirmation expires in 30 seconds."
            )

            view = CleanupConfirmView(
                allowed_user_id=interaction.user.id,
                channel=interaction.channel,
                amount=None,
                delete_all=True
            )

            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )

            return


        # =============================================
        # LIMITED CLEANUP CONFIRMATION
        # =============================================

        embed = discord.Embed(
            title="🧹 Confirm Cleanup",
            description=(
                f"Quasar will attempt to delete "
                f"**{amount} recent messages** "
                f"in {interaction.channel.mention}.\n\n"
                "Do you want to continue?"
            ),
            color=discord.Color.orange()
        )

        embed.set_footer(
            text="This confirmation expires in 30 seconds."
        )

        view = CleanupConfirmView(
            allowed_user_id=interaction.user.id,
            channel=interaction.channel,
            amount=amount,
            delete_all=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )


class CleanupConfirmView(
    discord.ui.View
):

    def __init__(
        self,
        allowed_user_id: int,
        channel: discord.TextChannel,
        amount: int | None,
        delete_all: bool
    ):

        super().__init__(timeout=30)

        self.allowed_user_id = allowed_user_id
        self.channel = channel
        self.amount = amount
        self.delete_all = delete_all


    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id != self.allowed_user_id:

            await interaction.response.send_message(
                "❌ Only the person who started "
                "the cleanup can confirm it.",
                ephemeral=True
            )

            return False

        return True


    # =============================================
    # CONFIRM BUTTON
    # =============================================

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.danger,
        emoji="🗑️"
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        deleted_count = 0

        try:

            # =========================================
            # LIMITED CLEANUP
            # =========================================

            if not self.delete_all:

                deleted = await self.channel.purge(
                    limit=self.amount
                )

                deleted_count = len(deleted)

                await interaction.followup.send(
                    (
                        f"🧹 Cleanup complete.\n\n"
                        f"Deleted **{deleted_count}** "
                        f"messages."
                    ),
                    ephemeral=True
                )

                return


            # =========================================
            # DELETE ALL
            # =========================================

            async for message in self.channel.history(
                limit=None
            ):

                try:

                    await message.delete()

                    deleted_count += 1

                    # Avoid hammering Discord's API.
                    await asyncio.sleep(0.15)

                except discord.NotFound:

                    continue

                except discord.Forbidden:

                    await interaction.followup.send(
                        (
                            "❌ I lost permission while "
                            "deleting messages.\n\n"
                            f"Deleted so far: "
                            f"**{deleted_count}**"
                        ),
                        ephemeral=True
                    )

                    return

                except discord.HTTPException:

                    await asyncio.sleep(1)


            await interaction.followup.send(
                (
                    "🧹 **Cleanup complete.**\n\n"
                    f"Deleted **{deleted_count}** "
                    f"messages."
                ),
                ephemeral=True
            )


        except discord.Forbidden:

            await interaction.followup.send(
                (
                    "❌ I don't have permission "
                    "to delete messages in this channel."
                ),
                ephemeral=True
            )


        except discord.HTTPException as e:

            await interaction.followup.send(
                (
                    "❌ Discord returned an error:\n"
                    f"`{e}`"
                ),
                ephemeral=True
            )


        except Exception as e:

            await interaction.followup.send(
                (
                    "❌ Unexpected error:\n"
                    f"`{type(e).__name__}: {e}`"
                ),
                ephemeral=True
            )


        finally:

            self.stop()


    # =============================================
    # CANCEL BUTTON
    # =============================================

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        emoji="❌"
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="🛡️ Cleanup cancelled.",
            embed=None,
            view=None
        )

        self.stop()