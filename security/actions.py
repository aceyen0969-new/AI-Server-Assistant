from dataclasses import dataclass, field
from typing import Any

from security.policies import (
    get_safety_decision
)


# =========================================================
# ACTION REQUEST
# =========================================================

@dataclass
class ActionRequest:

    # -----------------------------------------------------
    # WHAT ACTION IS BEING REQUESTED?
    # -----------------------------------------------------

    action: str

    # -----------------------------------------------------
    # WHO / WHAT IS THE TARGET?
    # -----------------------------------------------------

    target_id: int | None = None

    target_name: str | None = None

    # -----------------------------------------------------
    # WHY IS THE ACTION BEING REQUESTED?
    # -----------------------------------------------------

    reason: str = ""

    # -----------------------------------------------------
    # EXTRA DATA
    # -----------------------------------------------------
    # Examples:
    #
    # {
    #     "category_id": 123456789
    # }
    #
    # or
    #
    # {
    #     "channel_name": "gaming"
    # }
    # -----------------------------------------------------

    data: dict[str, Any] = field(
        default_factory=dict
    )


# =========================================================
# EVALUATE ACTION
# =========================================================

def evaluate_action(request: ActionRequest):

    decision = get_safety_decision(
        request.action
    )

    return {
        "action": request.action,

        "target_id": request.target_id,

        "target_name": request.target_name,

        "reason": request.reason,

        "data": request.data,

        "policy": decision["policy"],

        "allowed": decision["allowed"],

        "requires_approval": (
            decision["requires_approval"]
        )
    }


# =========================================================
# CHECK IF ACTION CAN EXECUTE AUTOMATICALLY
# =========================================================

def can_execute_automatically(
    request: ActionRequest
):

    decision = evaluate_action(
        request
    )

    return (
        decision["allowed"]
        and not decision["requires_approval"]
    )


# =========================================================
# CHECK IF ACTION NEEDS APPROVAL
# =========================================================

def needs_approval(
    request: ActionRequest
):

    decision = evaluate_action(
        request
    )

    return decision["requires_approval"]


# =========================================================
# CHECK IF ACTION IS SAFE TO EXECUTE
# =========================================================

def is_allowed(
    request: ActionRequest
):

    decision = evaluate_action(
        request
    )

    return decision["allowed"]
