from collections import defaultdict


def _get_channels(guild):
    """Return the guild's available channels safely."""
    channels = getattr(guild, "channels", [])

    if not isinstance(channels, (list, tuple)):
        return []

    return list(channels)


def _is_category(channel):
    """Identify category channels without relying on channel names."""
    return hasattr(channel, "channels") and not isinstance(
        getattr(channel, "channels", None),
        (str, bytes),
    )


def _channel_type(channel):
    """Return a readable channel type."""
    if _is_category(channel):
        return "category"

    type_name = type(channel).__name__.lower()

    if "text" in type_name:
        return "text"

    if "voice" in type_name:
        return "voice"

    if "forum" in type_name:
        return "forum"

    if "stage" in type_name:
        return "stage"

    if "thread" in type_name:
        return "thread"

    if "category" in type_name:
        return "category"

    channel_type = getattr(channel, "type", None)

    if channel_type is not None:
        return str(channel_type)

    return "unknown"


def _get_category_id(channel):
    """Return the parent category ID when available."""
    category_id = getattr(channel, "category_id", None)

    if category_id is not None:
        return category_id

    category = getattr(channel, "category", None)

    if category is not None:
        return getattr(category, "id", None)

    return None


def build_server_snapshot(guild):
    """
    Build a structured snapshot of a Discord server's layout.

    This function only reads cached guild and channel information.
    It does not modify the server or read message content.
    """
    if guild is None:
        raise ValueError("guild is required.")

    channels = _get_channels(guild)

    categories = [
        channel
        for channel in channels
        if _is_category(channel)
    ]

    regular_channels = [
        channel
        for channel in channels
        if not _is_category(channel)
    ]

    category_ids = {
        getattr(category, "id", None)
        for category in categories
    }

    category_details = []

    for category in categories:
        child_channels = getattr(category, "channels", [])

        if not isinstance(child_channels, (list, tuple)):
            child_channels = []

        category_details.append({
            "id": getattr(category, "id", None),
            "name": str(getattr(category, "name", "Unknown")),
            "channel_count": len(child_channels),
            "channel_names": [
                str(getattr(channel, "name", "Unknown"))
                for channel in child_channels
            ],
        })

    channel_details = []

    for channel in regular_channels:
        category_id = _get_category_id(channel)

        channel_details.append({
            "id": getattr(channel, "id", None),
            "name": str(getattr(channel, "name", "Unknown")),
            "type": _channel_type(channel),
            "category_id": category_id,
            "has_category": (
                category_id is not None
                and category_id in category_ids
            ),
        })

    return {
        "guild_id": getattr(guild, "id", None),
        "guild_name": str(getattr(guild, "name", "Unknown Server")),
        "channel_count": len(regular_channels),
        "category_count": len(categories),
        "channels": channel_details,
        "categories": category_details,
    }


def detect_structure_issues(snapshot):
    """
    Detect possible server-organization problems.

    Findings are suggestions, not instructions to modify the server.
    """
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a dictionary.")

    channels = snapshot.get("channels", [])
    categories = snapshot.get("categories", [])

    if not isinstance(channels, list):
        raise ValueError("snapshot channels must be a list.")

    if not isinstance(categories, list):
        raise ValueError("snapshot categories must be a list.")

    findings = []

    # --------------------------------------------
    # Empty categories
    # --------------------------------------------

    for category in categories:
        if not isinstance(category, dict):
            continue

        channel_count = category.get("channel_count")

        if channel_count == 0:
            name = str(category.get("name", "Unknown"))
            category_id = category.get("id")

            findings.append({
                "code": "empty_category",
                "severity": "low",
                "title": f"Empty category: {name}",
                "description": (
                    f"The category '{name}' currently has no channels."
                ),
                "evidence": {
                    "category_id": category_id,
                    "channel_count": 0,
                },
                "recommendation": (
                    "Review whether this category is still needed. "
                    "It may be intentionally reserved for future use."
                ),
            })

    # --------------------------------------------
    # Uncategorized channels
    # --------------------------------------------

    for channel in channels:
        if not isinstance(channel, dict):
            continue

        if channel.get("category_id") is None:
            name = str(channel.get("name", "Unknown"))
            channel_type = str(channel.get("type", "unknown"))

            findings.append({
                "code": "uncategorized_channel",
                "severity": "low",
                "title": f"Uncategorized channel: {name}",
                "description": (
                    f"The {channel_type} channel '{name}' "
                    "is not assigned to a category."
                ),
                "evidence": {
                    "channel_id": channel.get("id"),
                    "channel_type": channel_type,
                    "category_id": None,
                },
                "recommendation": (
                    "Review whether this channel would benefit from "
                    "being placed in an appropriate category. "
                    "Some channels are intentionally left uncategorized."
                ),
            })

    # --------------------------------------------
    # Possible duplicate channel names
    # --------------------------------------------

    channels_by_name = defaultdict(list)

    for channel in channels:
        if not isinstance(channel, dict):
            continue

        name = channel.get("name")

        if not isinstance(name, str) or not name.strip():
            continue

        normalized_name = name.strip().casefold()

        channels_by_name[normalized_name].append(channel)

    for normalized_name, matching_channels in channels_by_name.items():
        if len(matching_channels) < 2:
            continue

        # Avoid reporting duplicates across different channel types.
        channels_by_type = defaultdict(list)

        for channel in matching_channels:
            channels_by_type[
                channel.get("type", "unknown")
            ].append(channel)

        for channel_type, same_type_channels in channels_by_type.items():
            if len(same_type_channels) < 2:
                continue

            names = [
                {
                    "id": channel.get("id"),
                    "name": channel.get("name"),
                }
                for channel in same_type_channels
            ]

            display_name = str(
                same_type_channels[0].get("name", normalized_name)
            )

            findings.append({
                "code": "possible_duplicate_channel_name",
                "severity": "low",
                "title": f"Possible duplicate name: {display_name}",
                "description": (
                    f"{len(same_type_channels)} channels of type "
                    f"'{channel_type}' share the same name, ignoring "
                    "capitalization and surrounding whitespace."
                ),
                "evidence": {
                    "normalized_name": normalized_name,
                    "channel_type": channel_type,
                    "channels": names,
                },
                "recommendation": (
                    "Review whether these channels have distinct purposes. "
                    "Keep the names if the duplication is intentional."
                ),
            })

    return findings


def analyze_server_structure(guild):
    snapshot = build_server_snapshot(guild)

    print(
        "ANALYTICS SNAPSHOT DEBUG: "
        f"guild={snapshot['guild_name']!r}, "
        f"guild_id={snapshot['guild_id']}, "
        f"total_cached_channels={len(_get_channels(guild))}, "
        f"regular_channels={snapshot['channel_count']}, "
        f"categories={snapshot['category_count']}, "
        f"snapshot_channel_entries={len(snapshot['channels'])}, "
        f"snapshot_category_entries={len(snapshot['categories'])}",
        flush=True,
    )

    findings = detect_structure_issues(snapshot)

    severity_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    findings.sort(
        key=lambda finding: (
            severity_order.get(finding["severity"], 99),
            finding["code"],
            finding["title"].casefold(),
        )
    )

    return {
        "snapshot": snapshot,
        "findings": findings,
        "finding_count": len(findings),
        "summary": {
            "channel_count": snapshot["channel_count"],
            "category_count": snapshot["category_count"],
            "finding_count": len(findings),
        },
    }