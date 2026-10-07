from analytics.database import get_objectives


def get_active_objectives(
    guild_id: int,
):
    return get_objectives(
        guild_id=guild_id,
        status="active",
        limit=50,
    )


def build_objective_context(
    guild_id: int,
):
    objectives = get_active_objectives(
        guild_id
    )

    return [
        {
            "id": objective["id"],
            "objective": objective["objective"],
            "description": objective["description"] or "",
            "priority": objective["priority"],
        }
        for objective in objectives
    ]