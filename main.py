import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from commands import ping
from commands import serverinfo
from commands import serverstats
from commands import channels
from ai import assistant


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")


# =========================================================
# DISCORD BOT
# =========================================================

intents = discord.Intents.default()

intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# LOAD FEATURES
# =========================================================

async def load_features():

    await ping.setup(bot)

    await serverinfo.setup(bot)

    await serverstats.setup(bot)

    await channels.setup(bot)

    await assistant.setup(bot)


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():

    print("----------------------------------------")
    print(f"Logged in as {bot.user}")
    print(f"Connected to {len(bot.guilds)} server(s)")
    print("----------------------------------------")

    try:

        synced = await bot.tree.sync()

        print(f"Synced {len(synced)} slash command(s)")

    except Exception as e:

        print("Command sync error:")
        print(e)


# =========================================================
# START BOT
# =========================================================

async def main():

    async with bot:

        await load_features()

        await bot.start(DISCORD_TOKEN)


print("Starting AI Server Assistant...")

import asyncio

asyncio.run(main())