from security.actions import (
    ActionRequest,
    evaluate_action,
    can_execute_automatically,
    needs_approval,
    is_allowed
)


# =========================================================
# AUTOMATIC ACTION
# =========================================================

spam_request = ActionRequest(

    action="delete_spam",

    target_id=123456789,

    target_name="Spam Message",

    reason="Obvious repeated spam message."
)


print("AUTOMATIC ACTION")
print(
    evaluate_action(
        spam_request
    )
)

print(
    "Can execute:",
    can_execute_automatically(
        spam_request
    )
)

print(
    "Needs approval:",
    needs_approval(
        spam_request
    )
)

print(
    "Allowed:",
    is_allowed(
        spam_request
    )
)


print()


# =========================================================
# APPROVAL ACTION
# =========================================================

ban_request = ActionRequest(

    action="ban_member",

    target_id=987654321,

    target_name="ExampleUser",

    reason="Repeated serious rule violations."
)


print("APPROVAL ACTION")
print(
    evaluate_action(
        ban_request
    )
)

print(
    "Can execute:",
    can_execute_automatically(
        ban_request
    )
)

print(
    "Needs approval:",
    needs_approval(
        ban_request
    )
)

print(
    "Allowed:",
    is_allowed(
        ban_request
    )
)


print()


# =========================================================
# UNKNOWN ACTION
# =========================================================

unknown_request = ActionRequest(

    action="destroy_server",

    reason="AI-generated unknown action."
)


print("UNKNOWN ACTION")
print(
    evaluate_action(
        unknown_request
    )
)

print(
    "Can execute:",
    can_execute_automatically(
        unknown_request
    )
)

print(
    "Needs approval:",
    needs_approval(
        unknown_request
    )
)

print(
    "Allowed:",
    is_allowed(
        unknown_request
    )
)
