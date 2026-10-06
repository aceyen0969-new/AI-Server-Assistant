import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

from commands import ping
from commands import serverinfo
from commands import serverstats
from commands import channels
from commands import organize
from commands import aistatus
from commands import approvaltest
from commands import cleanup
from commands import analytics

from moderation.moderator import moderation_manager

from ai import assistant

from analytics import observer
from analytics.database import initialize_database


load_dotenv()


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


if not DISCORD_TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing from .env"
    )


intents = discord.Intents.default()

intents.members = True
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


async def load_features():

    await ping.setup(bot)

    await serverinfo.setup(bot)

    await serverstats.setup(bot)

    await channels.setup(bot)

    await organize.setup(bot)

    await assistant.setup(bot)

    await aistatus.setup(bot)

    await approvaltest.setup(bot)

    await cleanup.setup(bot)

    await analytics.setup(bot)


@bot.event
async def on_ready():

    print("----------------------------------------")

    print(
        f"Logged in as {bot.user}"
    )

    print(
        f"Connected to {len(bot.guilds)} server(s)"
    )

    print("----------------------------------------")

    try:

        synced = await bot.tree.sync()

        print(
            f"Synced {len(synced)} slash command(s)"
        )

    except Exception as e:

        print("Command sync error:")

        print(e)


@bot.event
async def on_message(message):

    await moderation_manager.handle_message(
        message
    )

    await observer.handle_message(
        message
    )

    await assistant.handle_message(
        message
    )

    await bot.process_commands(
        message
    )


async def main():

    initialize_database()

    async with bot:

        await load_features()

        await bot.start(
            DISCORD_TOKEN
        )


print(
    "Starting AI Server Assistant..."
)


asyncio.run(
    main()
)