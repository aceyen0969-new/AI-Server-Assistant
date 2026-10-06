import discord

from ai.manager import ask_ai
from utils.messages import send_long_message


async def setup(bot):
    pass


async def handle_message(message: discord.Message):

    if message.author.bot:
        return

    if message.guild is None:
        return

    if message.channel.name != "ai-assistant":
        return

    if not message.content.strip():
        return

    prompt = message.content.strip()

    history = []

    # Keep a small conversation history per channel.
    if not hasattr(handle_message, "history"):
        handle_message.history = {}

    channel_history = handle_message.history.setdefault(
        message.channel.id,
        []
    )

    result = await ask_ai(
        prompt,
        history=channel_history
    )

    answer = result.get("answer")
    provider = result.get("provider")

    if not answer:
        await message.channel.send(
            "❌ All AI providers are currently unavailable."
        )
        return

    await send_long_message(
        message.channel,
        answer
    )

    channel_history.append({
        "role": "user",
        "content": prompt
    })

    channel_history.append({
        "role": "assistant",
        "content": answer
    })

    # Keep the latest 20 messages.
    if len(channel_history) > 20:
        del channel_history[:-20]

    print("----------------------------------------")
    print(f"🤖 AI Provider used: {provider}")
    print(
        f"🧠 Conversation memory: "
        f"{len(channel_history)} messages"
    )
    print("----------------------------------------")