from copy import deepcopy
from dataclasses import dataclass, field
import time
from typing import Any


DEFAULT_EXPIRATION_SECONDS = 300


@dataclass
class ApprovalRequest:
    request_id: str
    action: str
    target_id: int | None = None
    target_name: str | None = None
    reason: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    expires_at: float = 0.0
    approved: bool = False
    cancelled: bool = False

    # Execution lifecycle
    status: str = "pending"
    executing: bool = False
    completed: bool = False
    execution_succeeded: bool | None = None

    # Immutable-in-practice snapshot captured at approval time
    approved_snapshot: dict[str, Any] | None = None


approval_requests: dict[str, ApprovalRequest] = {}


def create_approval_request(
    request_id: str,
    action: str,
    target_id: int | None = None,
    target_name: str | None = None,
    reason: str = "",
    data: dict[str, Any] | None = None,
    expires_in: float = DEFAULT_EXPIRATION_SECONDS,
) -> ApprovalRequest:
    if not isinstance(expires_in, (int, float)):
        raise TypeError("expires_in must be a number.")

    if isinstance(expires_in, bool) or expires_in <= 0:
        raise ValueError("expires_in must be positive.")

    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be a non-empty string.")

    if request_id in approval_requests:
        raise ValueError("request_id already exists.")

    if not isinstance(action, str) or not action.strip():
        raise ValueError("action must be a non-empty string.")

    if not isinstance(reason, str):
        raise TypeError("reason must be a string.")

    if data is not None and not isinstance(data, dict):
        raise TypeError("data must be a dictionary.")

    now = time.time()

    request = ApprovalRequest(
        request_id=request_id,
        action=action,
        target_id=target_id,
        target_name=target_name,
        reason=reason,
        data=deepcopy(data) if data is not None else {},
        created_at=now,
        expires_at=now + expires_in,
    )

    approval_requests[request_id] = request
    return request


def get_approval_request(
    request_id: str,
) -> ApprovalRequest | None:
    return approval_requests.get(request_id)


def is_expired(request_id: str) -> bool:
    request = get_approval_request(request_id)

    if request is None:
        return False

    return (
        request.expires_at > 0
        and time.time() >= request.expires_at
    )


def approve_request(request_id: str) -> bool:
    request = get_approval_request(request_id)

    if request is None:
        return False

    if is_expired(request_id):
        request.status = "expired"
        return False

    if (
        request.cancelled
        or request.approved
        or request.status != "pending"
    ):
        return False

    # Capture the exact request contents at approval time.
    request.approved_snapshot = {
        "action": request.action,
        "target_id": request.target_id,
        "target_name": request.target_name,
        "reason": request.reason,
        "data": deepcopy(request.data),
    }

    request.approved = True
    request.status = "approved"
    return True


def claim_approved_request(
    request_id: str,
    action: dict[str, Any],
    reason: str | None,
) -> bool:
    """Atomically claim an approved request for one execution."""

    request = get_approval_request(request_id)

    if request is None:
        return False

    if is_expired(request_id):
        request.status = "expired"
        return False

    if (
        not request.approved
        or request.cancelled
        or request.executing
        or request.completed
        or request.status != "approved"
    ):
        return False

    snapshot = request.approved_snapshot

    if not isinstance(snapshot, dict):
        return False

    if not isinstance(action, dict):
        return False

    action_type = action.get("action")
    action_data = {
        key: value
        for key, value in action.items()
        if key != "action"
    }

    if action_type != snapshot["action"]:
        return False

    if action_data != snapshot["data"]:
        return False

    if request.action != snapshot["action"]:
        return False

    if request.target_id != snapshot["target_id"]:
        return False

    if request.target_name != snapshot["target_name"]:
        return False

    if request.reason != snapshot["reason"]:
        return False

    if request.data != snapshot["data"]:
        return False

    if reason != snapshot["reason"]:
        return False

    # No await occurs before this state transition.
    # A second interaction in the same event loop cannot
    # claim this request once it is marked as executing.
    request.executing = True
    request.status = "executing"
    return True


def complete_approval_request(
    request_id: str,
    success: bool,
) -> bool:
    request = get_approval_request(request_id)

    if request is None or not request.executing:
        return False

    request.executing = False
    request.completed = True
    request.execution_succeeded = bool(success)
    request.status = "completed" if success else "failed"
    return True


def cancel_request(request_id: str) -> bool:
    request = get_approval_request(request_id)

    if request is None:
        return False

    if is_expired(request_id):
        request.status = "expired"
        return False

    if (
        request.approved
        or request.cancelled
        or request.executing
        or request.completed
        or request.status != "pending"
    ):
        return False

    request.cancelled = True
    request.status = "cancelled"
    return True


def is_approved(request_id: str) -> bool:
    request = get_approval_request(request_id)
    return request is not None and request.approved


def is_cancelled(request_id: str) -> bool:
    request = get_approval_request(request_id)
    return request is not None and request.cancelled