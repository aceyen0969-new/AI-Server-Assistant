
# =========================================================
# AI SERVER ASSISTANT
# ACTION POLICIES
# =========================================================
#
# The AI may request actions, but Python controls policy.
# Approval-required actions must never execute automatically.
# =========================================================


ACTION_POLICIES = {
    # Automatic moderation actions
    "delete_spam": "automatic",
    "warn_member": "automatic",
    "timeout_member": "automatic",

    # Actions requiring explicit approval
    "move_channel": "approval",
    "create_channel": "approval",
    "rename_channel": "approval",
    "kick_member": "approval",
    "ban_member": "approval",
    "delete_channel": "approval",
    "manage_role": "approval",
    "change_permissions": "approval",
}


def get_action_policy(action):
    """Return automatic, approval, or unknown."""
    return ACTION_POLICIES.get(action, "unknown")


def is_automatic(action):
    return get_action_policy(action) == "automatic"


def requires_approval(action):
    return get_action_policy(action) == "approval"


def is_known_action(action):
    return action in ACTION_POLICIES


def get_safety_decision(action):
    """
    Describe whether an action is allowed to execute
    automatically or is eligible for an approval workflow.

    The executor must still independently validate approval.
    """
    policy = get_action_policy(action)

    if policy == "automatic":
        return {
            "action": action,
            "policy": "automatic",
            "allowed": True,
            "requires_approval": False,
        }

    if policy == "approval":
        return {
            "action": action,
            "policy": "approval",
            "allowed": True,
            "requires_approval": True,
        }

    return {
        "action": action,
        "policy": "unknown",
        "allowed": False,
        "requires_approval": True,
    }