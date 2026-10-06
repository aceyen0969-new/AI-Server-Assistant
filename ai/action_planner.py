import json
import re

import discord

from ai.provider_router import ask_with_fallback


ALLOWED_ACTIONS = {
    "move_channel",
    "rename_channel",
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

    if not isinstance(
        name,
        str,
    ):
        return None

    # Prefer an exact-case match.
    exact_matches = []

    for channel in guild.channels:

        if not isinstance(
            channel,
            (
                discord.TextChannel,
                discord.VoiceChannel,
            ),
        ):
            continue

        if channel.name == name:
            exact_matches.append(channel)

    if len(exact_matches) == 1:
        return exact_matches[0]

    # Fall back to case-insensitive matching.
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
    """Find a category by name."""

    if not isinstance(
        name,
        str,
    ):
        return None

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

Your ONLY job is to convert the user's request into safe,
structured Discord actions.

USER REQUEST:
{user_request}

SERVER CONTEXT:
{server_context}

ALLOWED ACTIONS:
- move_channel
- rename_channel

IMPORTANT:

The server context contains the REAL Discord channels
and categories.

The Python application will resolve channel and category
names into real Discord IDs.

NEVER invent Discord IDs.

========================================
NAME MATCHING
========================================

When multiple channels have names that differ only by
capitalization, use the exact capitalization provided
by the user.

Example:

Server:
- general
- General

User says:
"general"

Select:
"general"

User says:
"General"

Select:
"General"

Do NOT return an empty action merely because two channel
names differ only by capitalization.

========================================
MOVE CHANNEL
========================================

For move_channel:

The user wants an existing text or voice channel
moved into an existing category.

Required fields:

- action
- channel_name
- category_name

Example:

{{
    "actions": [
        {{
            "action": "move_channel",
            "channel_name": "gaming",
            "category_name": "Text Channels"
        }}
    ]
}}

Rules:

1. Find the requested channel by name.
2. Match channel names case-insensitively unless exact
   capitalization identifies one specific channel.
3. The channel must be a text or voice channel.
4. Find the requested destination by category name.
5. The destination MUST actually be a category.
6. Match category names case-insensitively.
7. Never use a text or voice channel as a category.
8. Never invent IDs.
9. Never substitute a different category.
10. If the requested channel or category does not exist,
    return:

{{"actions": []}}

========================================
RENAME CHANNEL
========================================

For rename_channel:

The user wants an existing text or voice channel
to receive a new name.

Required fields:

- action
- channel_name
- new_name

Example:

{{
    "actions": [
        {{
            "action": "rename_channel",
            "channel_name": "general",
            "new_name": "chat"
        }}
    ]
}}

Rules:

1. Find the existing channel by name.
2. Match the channel using the user's capitalization
   when that distinguishes between channels.
3. The channel must be a text or voice channel.
4. The new_name must be a non-empty string.
5. Do not invent the existing channel.
6. Do not return a Discord ID.
7. If the requested channel does not exist,
   return:

{{"actions": []}}

========================================
OUTPUT
========================================

Return ONLY valid JSON.

You may return multiple actions if the user's request
clearly asks for multiple independent changes.

Example:

{{
    "actions": [
        {{
            "action": "rename_channel",
            "channel_name": "general",
            "new_name": "chat"
        }},
        {{
            "action": "move_channel",
            "channel_name": "gaming",
            "category_name": "Text Channels"
        }}
    ]
}}

If the request cannot be safely converted into valid
actions, return:

{{"actions": []}}

NEVER perform the Discord action yourself.

ONLY return structured JSON.
"""


def validate_action(
    action: dict,
    guild: discord.Guild,
) -> bool:
    """Validate one resolved action."""

    if not isinstance(
        action,
        dict,
    ):
        return False

    action_type = action.get(
        "action"
    )

    if action_type not in ALLOWED_ACTIONS:
        return False

    if action_type == "move_channel":

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

    if action_type == "rename_channel":

        channel_id = action.get(
            "channel_id"
        )

        new_name = action.get(
            "new_name"
        )

        if not isinstance(
            channel_id,
            int,
        ):
            return False

        if not isinstance(
            new_name,
            str,
        ):
            return False

        new_name = new_name.strip()

        if not new_name:
            return False

        if len(new_name) > 100:
            return False

        channel = guild.get_channel(
            channel_id
        )

        if channel is None:
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
    """Resolve AI-provided names into real Discord IDs."""

    if not isinstance(
        action,
        dict,
    ):
        return None

    action_type = action.get(
        "action"
    )

    if action_type == "move_channel":

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

    if action_type == "rename_channel":

        channel_name = action.get(
            "channel_name"
        )

        new_name = action.get(
            "new_name"
        )

        if not isinstance(
            channel_name,
            str,
        ):
            return None

        if not isinstance(
            new_name,
            str,
        ):
            return None

        new_name = new_name.strip()

        if not new_name:
            return None

        if len(new_name) > 100:
            return None

        channel = find_channel_by_name(
            guild,
            channel_name,
        )

        if channel is None:
            return None

        return {
            "action": "rename_channel",
            "channel_id": channel.id,
            "new_name": new_name,
        }

    return None


async def plan_actions(
    guild: discord.Guild,
    user_request: str,
):
    """Convert a natural-language request into validated actions."""

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

        # Backwards-compatible support for actions
        # that already contain valid Discord IDs.

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