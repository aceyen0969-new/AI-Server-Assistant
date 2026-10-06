# =========================================================
# AI SERVER ASSISTANT
# ACTION POLICIES
# =========================================================
#
# IMPORTANT:
#
# The AI can REQUEST an action.
#
# The AI does NOT decide whether the action is allowed.
#
# This file is controlled by Python and acts as the
# server's safety policy.
#
# =========================================================


# =========================================================
# ACTION TYPES
# =========================================================

ACTION_POLICIES = {

    # -----------------------------------------------------
    # AUTOMATIC ACTIONS
    # -----------------------------------------------------
    # These actions can eventually happen automatically
    # after the appropriate executor is implemented.
    # -----------------------------------------------------

    "delete_spam": "automatic",

    "warn_member": "automatic",

    "timeout_member": "automatic",


    # -----------------------------------------------------
    # ACTIONS REQUIRING APPROVAL
    # -----------------------------------------------------
    # These actions must NEVER execute immediately.
    # They require explicit owner/admin confirmation.
    # -----------------------------------------------------

    "move_channel": "approval",

    "create_channel": "approval",

    "rename_channel": "approval",

    "kick_member": "approval",

    "ban_member": "approval",

    "delete_channel": "approval",

    "manage_role": "approval",

    "change_permissions": "approval"
}


# =========================================================
# GET ACTION POLICY
# =========================================================

def get_action_policy(action):

    """
    Return the policy assigned to an action.

    Possible results:

    "automatic"
    "approval"
    "unknown"
    """

    return ACTION_POLICIES.get(
        action,
        "unknown"
    )


# =========================================================
# CHECK IF ACTION IS AUTOMATIC
# =========================================================

def is_automatic(action):

    return (
        get_action_policy(action)
        == "automatic"
    )


# =========================================================
# CHECK IF ACTION REQUIRES APPROVAL
# =========================================================

def requires_approval(action):

    return (
        get_action_policy(action)
        == "approval"
    )


# =========================================================
# CHECK IF ACTION IS KNOWN
# =========================================================

def is_known_action(action):

    return action in ACTION_POLICIES


# =========================================================
# SAFETY DECISION
# =========================================================

def get_safety_decision(action):

    """
    Return a structured safety decision.

    IMPORTANT:
    Unknown actions are DENIED.

    We never assume that an unknown action is safe.
    """

    policy = get_action_policy(action)


    # -----------------------------------------------------
    # AUTOMATIC
    # -----------------------------------------------------

    if policy == "automatic":

        return {
            "action": action,
            "policy": "automatic",
            "allowed": True,
            "requires_approval": False
        }


    # -----------------------------------------------------
    # APPROVAL REQUIRED
    # -----------------------------------------------------

    if policy == "approval":

        return {
            "action": action,
            "policy": "approval",
            "allowed": False,
            "requires_approval": True
        }


    # -----------------------------------------------------
    # UNKNOWN ACTION
    # -----------------------------------------------------
    # Fail closed.
    # -----------------------------------------------------

    return {
        "action": action,
        "policy": "unknown",
        "allowed": False,
        "requires_approval": True
    }
