from security.approval import (
    create_approval_request,
    get_approval_request,
    approve_request,
    cancel_request,
    is_approved,
    is_cancelled
)


request = create_approval_request(
    request_id="test-ban-001",
    action="ban_member",
    target_id=987654321,
    target_name="ExampleUser",
    reason="Repeated serious rule violations."
)

print("CREATED REQUEST")
print(request)

print()
print("GET REQUEST")
print(get_approval_request("test-ban-001"))

print()
print("BEFORE APPROVAL")
print("Approved:", is_approved("test-ban-001"))
print("Cancelled:", is_cancelled("test-ban-001"))

print()
print("APPROVING REQUEST")
print("Success:", approve_request("test-ban-001"))

print()
print("AFTER APPROVAL")
print("Approved:", is_approved("test-ban-001"))
print("Cancelled:", is_cancelled("test-ban-001"))

print()
print("TRYING TO CANCEL APPROVED REQUEST")
print("Success:", cancel_request("test-ban-001"))
