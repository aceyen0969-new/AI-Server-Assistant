from dataclasses import dataclass
import time


@dataclass
class ApprovalRequest:
    request_id: str
    action: str
    target_id: int | None = None
    target_name: str | None = None
    reason: str = ""
    created_at: float = 0.0
    approved: bool = False
    cancelled: bool = False


approval_requests = {}


def create_approval_request(
    request_id: str,
    action: str,
    target_id: int | None = None,
    target_name: str | None = None,
    reason: str = ""
):
    request = ApprovalRequest(
        request_id=request_id,
        action=action,
        target_id=target_id,
        target_name=target_name,
        reason=reason,
        created_at=time.time()
    )

    approval_requests[request_id] = request

    return request


def get_approval_request(request_id: str):
    return approval_requests.get(request_id)


def approve_request(request_id: str):
    request = get_approval_request(request_id)

    if request is None:
        return False

    if request.cancelled:
        return False

    if request.approved:
        return False

    request.approved = True
    return True


def cancel_request(request_id: str):
    request = get_approval_request(request_id)

    if request is None:
        return False

    if request.approved:
        return False

    if request.cancelled:
        return False

    request.cancelled = True
    return True


def is_approved(request_id: str):
    request = get_approval_request(request_id)

    if request is None:
        return False

    return request.approved


def is_cancelled(request_id: str):
    request = get_approval_request(request_id)

    if request is None:
        return False

    return request.cancelled
