import json

import discord

from ai.providers import ask_openrouter_json


ALLOWED_ACTIONS = {
    "move_channel",
}


def build_server_context(guild: discord.Guild) -> str:
    """Build a compact description of the Discord server."""

    channels = []

    for channel in guild.channels:
        if isinstance(channel, discord.CategoryChannel):
            channels.append(
                {
                    "id": channel.id,
                    "name": channel.name,
                    "type": "category",
                }
            )

        elif isinstance(channel, discord.TextChannel):
            channels.append(
                {
                    "id": channel.id,
                    "name": channel.name,
                    "type": "text",
                    "category_id": channel.category_id,
                    "category_name": (
                        channel.category.name
                        if channel.category
                        else None
                    ),
                }
            )

        elif isinstance(channel, discord.VoiceChannel):
            channels.append(
                {
                    "id": channel.id,
                    "name": channel.name,
                    "type": "voice",
                    "category_id": channel.category_id,
                    "category_name": (
                        channel.category.name
                        if channel.category
                        else None
                    ),
                }
            )

    return json.dumps(
        {
            "guild_id": guild.id,
            "guild_name": guild.name,
            "channels": channels,
        },
        indent=2,
    )


def build_planner_prompt(
    guild: discord.Guild,
    user_request: str,
) -> str:
    """Create the prompt used by the action planner."""

    server_context = build_server_context(guild)

    return f"""
You are the action planner for a Discord server management assistant.

Your job is to convert the user's request into safe,
structured Discord actions.

USER REQUEST:
{user_request}

SERVER CONTEXT:
{server_context}

ALLOWED ACTIONS:
- move_channel

OUTPUT FORMAT:
Return ONLY valid JSON.

Use this exact structure:

{{
    "actions": [
        {{
            "action": "move_channel",
            "channel_id": 123456789,
            "category_id": 987654321
        }}
    ]
}}

RULES:
1. Only use actions from the allowed action list.
2. Use real channel IDs from the server context.
3. Never invent IDs.
4. Do not perform the action yourself.
5. Do not include explanations outside the JSON.
6. If the request cannot be safely converted into an allowed action,
   return:
   {{"actions": []}}
"""


def validate_action(
    action: dict,
    guild: discord.Guild,
) -> bool:
    """Validate one AI-generated action."""

    if not isinstance(action, dict):
        return False

    if action.get("action") not in ALLOWED_ACTIONS:
        return False

    if action["action"] == "move_channel":
        channel_id = action.get("channel_id")
        category_id = action.get("category_id")

        if not isinstance(channel_id, int):
            return False

        if not isinstance(category_id, int):
            return False

        channel = guild.get_channel(channel_id)
        category = guild.get_channel(category_id)

        if channel is None:
            return False

        if category is None:
            return False

        if not isinstance(category, discord.CategoryChannel):
            return False

        if not isinstance(
            channel,
            (
                discord.TextChannel,
                discord.VoiceChannel,
            ),
        ):
            return False

        return True

    return False


async def plan_actions(
    guild: discord.Guild,
    user_request: str,
):
    """
    Convert a natural-language request into
    validated Discord actions.
    """

    prompt = build_planner_prompt(
        guild,
        user_request,
    )

    try:
        result = await ask_openrouter_json(prompt)

    except Exception:
        return {
            "actions": [],
        }

    try:
        data = json.loads(result)

    except (json.JSONDecodeError, TypeError):
        return {
            "actions": [],
        }

    if not isinstance(data, dict):
        return {
            "actions": [],
        }

    raw_actions = data.get("actions", [])

    if not isinstance(raw_actions, list):
        return {
            "actions": [],
        }

    valid_actions = []

    for action in raw_actions:
        if validate_action(action, guild):
            valid_actions.append(action)

    return {
        "actions": valid_actions,
    }