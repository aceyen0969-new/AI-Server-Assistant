import json
import re

import discord

from ai.provider_router import ask_with_fallback


ALLOWED_ACTIONS = {
    "move_channel",
}


def build_server_context(
    guild: discord.Guild,
) -> str:
    """Build a compact description of the Discord server."""

    channels = []

    for channel in guild.channels:

        if isinstance(
            channel,
            discord.CategoryChannel,
        ):
            channels.append(
                {
                    "id": channel.id,
                    "name": channel.name,
                    "type": "category",
                }
            )

        elif isinstance(
            channel,
            discord.TextChannel,
        ):
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

        elif isinstance(
            channel,
            discord.VoiceChannel,
        ):
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


def normalize_name(name: str) -> str:
    """Normalize a Discord name for comparison."""

    return re.sub(
        r"\s+",
        " ",
        name.strip().lower(),
    )


def find_channel_by_name(
    guild: discord.Guild,
    name: str,
):
    """Find a text or voice channel by name."""

    normalized = normalize_name(name)

    matches = []

    for channel in guild.channels:

        if not isinstance(
            channel,
            (
                discord.TextChannel,
                discord.VoiceChannel,
            ),
        ):
            continue

        if normalize_name(channel.name) == normalized:
            matches.append(channel)

    if len(matches) == 1:
        return matches[0]

    return None


def find_category_by_name(
    guild: discord.Guild,
    name: str,
):
    """Find a category by its exact normalized name."""

    normalized = normalize_name(name)

    matches = []

    for channel in guild.channels:

        if not isinstance(
            channel,
            discord.CategoryChannel,
        ):
            continue

        if normalize_name(channel.name) == normalized:
            matches.append(channel)

    if len(matches) == 1:
        return matches[0]

    return None


def build_planner_prompt(
    guild: discord.Guild,
    user_request: str,
) -> str:
    """Create the prompt used by the action planner."""

    server_context = build_server_context(guild)

    return f"""
You are the action planner for a Discord server management assistant.

Your ONLY job is to convert the user's request into a
safe, structured Discord action.

USER REQUEST:
{user_request}

SERVER CONTEXT:
{server_context}

ALLOWED ACTIONS:
- move_channel

IMPORTANT:

The server context contains the REAL Discord channels
and categories.

For move_channel:

- channel_id MUST be the ID of the channel the user wants moved.
- category_id MUST be the ID of the destination category.
- Only objects with "type": "category" can be used as category_id.
- Text channels have "type": "text".
- Voice channels have "type": "voice".
- Never use a text channel as category_id.
- Never use a voice channel as category_id.
- Never invent IDs.

CATEGORY RULES:

1. If the user explicitly names a destination category,
   find that category by name.

2. The destination MUST have:
   "type": "category"

3. Match the category name case-insensitively.

4. NEVER use a channel with the same name as the requested
   category if that channel is not a category.

5. NEVER substitute a different category.

6. If the requested category does not exist,
   return:

{{"actions": []}}

CHANNEL RULES:

1. Find the requested channel by name.

2. Match the channel name case-insensitively.

3. The channel MUST have type "text" or "voice".

4. Never invent channel IDs.

5. If the requested channel does not exist,
   return:

{{"actions": []}}

OUTPUT:

Return ONLY valid JSON.

For a valid move:

{{
    "actions": [
        {{
            "action": "move_channel",
            "channel_id": 123456789,
            "category_id": 987654321
        }}
    ]
}}

If the request cannot be safely converted into a valid
move_channel action:

{{"actions": []}}

NEVER perform the Discord action yourself.
ONLY return the structured JSON.
"""


def validate_action(
    action: dict,
    guild: discord.Guild,
) -> bool:
    """Validate one AI-generated action."""

    if not isinstance(
        action,
        dict,
    ):
        return False

    if action.get("action") not in ALLOWED_ACTIONS:
        return False

    if action["action"] == "move_channel":

        channel_id = action.get(
            "channel_id"
        )

        category_id = action.get(
            "category_id"
        )

        if not isinstance(
            channel_id,
            int,
        ):
            return False

        if not isinstance(
            category_id,
            int,
        ):
            return False

        channel = guild.get_channel(
            channel_id
        )

        category = guild.get_channel(
            category_id
        )

        if channel is None:
            return False

        if category is None:
            return False

        if not isinstance(
            category,
            discord.CategoryChannel,
        ):
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


def resolve_action(
    action: dict,
    guild: discord.Guild,
) -> dict | None:
    """
    Replace AI-provided IDs with IDs resolved
    deterministically from the Discord server.

    This prevents the AI from inventing or choosing
    incorrect Discord IDs.
    """

    if not isinstance(
        action,
        dict,
    ):
        return None

    if action.get("action") != "move_channel":
        return None

    channel_name = action.get(
        "channel_name"
    )

    category_name = action.get(
        "category_name"
    )

    if not isinstance(
        channel_name,
        str,
    ):
        return None

    if not isinstance(
        category_name,
        str,
    ):
        return None

    channel = find_channel_by_name(
        guild,
        channel_name,
    )

    category = find_category_by_name(
        guild,
        category_name,
    )

    if channel is None:
        return None

    if category is None:
        return None

    return {
        "action": "move_channel",
        "channel_id": channel.id,
        "category_id": category.id,
    }


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

    print(
        "========== PLANNER REQUEST =========="
    )
    print(user_request)

    print(
        "========== SERVER CONTEXT =========="
    )
    print(
        build_server_context(guild)
    )

    print(
        "====================================="
    )

    provider_name, result = await ask_with_fallback(
        prompt
    )

    if result is None:

        print(
            "ACTION PLANNER: "
            "All AI providers failed."
        )

        return {
            "actions": [],
            "provider": None,
        }

    print(
        "========== AI RESULT =========="
    )
    print(result)
    print(
        "==============================="
    )

    try:

        data = json.loads(
            result
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ) as e:

        print(
            "ACTION PLANNER JSON ERROR:"
        )

        print(
            repr(e)
        )

        return {
            "actions": [],
            "provider": provider_name,
        }

    if not isinstance(
        data,
        dict,
    ):

        print(
            "ACTION PLANNER ERROR: "
            "AI response was not a JSON object."
        )

        return {
            "actions": [],
            "provider": provider_name,
        }

    raw_actions = data.get(
        "actions",
        [],
    )

    if not isinstance(
        raw_actions,
        list,
    ):

        print(
            "ACTION PLANNER ERROR: "
            "'actions' was not a list."
        )

        return {
            "actions": [],
            "provider": provider_name,
        }

    valid_actions = []

    for action in raw_actions:

        # New preferred format:
        #
        # {
        #     "action": "move_channel",
        #     "channel_name": "gaming",
        #     "category_name": "Text Channels"
        # }

        resolved = resolve_action(
            action,
            guild,
        )

        if resolved is not None:

            if validate_action(
                resolved,
                guild,
            ):
                valid_actions.append(
                    resolved
                )

            continue

        # Backwards-compatible support for
        # actions that already contain IDs.

        if validate_action(
            action,
            guild,
        ):
            valid_actions.append(
                action
            )

    if not valid_actions:

        print(
            "ACTION PLANNER: "
            "No valid actions returned."
        )

        print(
            "AI RESPONSE:"
        )

        print(
            result
        )

    else:

        print(
            f"ACTION PLANNER: "
            f"Using {provider_name}."
        )

    return {
        "actions": valid_actions,
        "provider": provider_name,
    }