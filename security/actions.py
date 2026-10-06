from dataclasses import dataclass, field
from typing import Any

from security.policies import (
    get_safety_decision
)


@dataclass
class ActionRequest:
    action: str
    target_id: int | None = None
    target_name: str | None = None
    reason: str = ""
    data: dict[str, Any] = field(
        default_factory=dict
    )


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
        "requires_approval": decision["requires_approval"]
    }


def can_execute_automatically(
    request: ActionRequest
):
    decision = evaluate_action(request)

    return (
        decision["policy"] == "automatic"
        and decision["allowed"]
        and not decision["requires_approval"]
    )


def can_execute_after_approval(
    request: ActionRequest
):
    decision = evaluate_action(request)

    return decision["policy"] in (
        "automatic",
        "approval"
    )


def needs_approval(
    request: ActionRequest
):
    decision = evaluate_action(request)

    return decision["requires_approval"]


def is_allowed(
    request: ActionRequest
):
    decision = evaluate_action(request)

    return decision["allowed"]
