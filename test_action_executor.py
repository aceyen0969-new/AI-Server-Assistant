import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ai.action_executor import _is_valid_approval
from security.approval import (
    approval_requests,
    create_approval_request,
    approve_request,
    claim_approved_request,
    complete_approval_request,
)


class TestActionExecutorSecurity(unittest.TestCase):

    def setUp(self):
        self.request_id = "test-request-123"

        self.action = {
            "action": "rename_channel",
            "channel_id": 12345,
            "new_name": "new-channel-name",
        }

        self.reason = "Testing approval security"

        self.request = SimpleNamespace(
            action="rename_channel",
            target_id=None,
            target_name=None,
            data={
                "channel_id": 12345,
                "new_name": "new-channel-name",
            },
            reason=self.reason,
            approved=True,
            cancelled=False,
            executing=False,
            completed=False,
            approved_snapshot={
                "action": "rename_channel",
                "target_id": None,
                "target_name": None,
                "reason": self.reason,
                "data": {
                    "channel_id": 12345,
                    "new_name": "new-channel-name",
                },
            },
        )

        self.request_patch = patch(
            "ai.action_executor.get_approval_request",
            return_value=self.request,
        )
        self.expired_patch = patch(
            "ai.action_executor.is_expired",
            return_value=False,
        )
        self.policy_patch = patch(
            "ai.action_executor.get_safety_decision",
            return_value={
                "policy": "approval",
                "allowed": True,
                "requires_approval": True,
            },
        )

        self.request_patch.start()
        self.expired_patch.start()
        self.policy_patch.start()
        self.addCleanup(patch.stopall)

    def check_action(self, **overrides):
        arguments = {
            "action": self.action,
            "reason": self.reason,
            "approval_request_id": self.request_id,
        }
        arguments.update(overrides)
        return _is_valid_approval(**arguments)

    def test_valid_approved_request_is_accepted(self):
        self.assertTrue(self.check_action())

    def test_missing_request_id_is_rejected(self):
        self.assertFalse(
            self.check_action(approval_request_id=None)
        )

    def test_unknown_request_is_rejected(self):
        with patch(
            "ai.action_executor.get_approval_request",
            return_value=None,
        ):
            self.assertFalse(self.check_action())

    def test_unapproved_request_is_rejected(self):
        self.request.approved = False
        self.assertFalse(self.check_action())

    def test_cancelled_request_is_rejected(self):
        self.request.cancelled = True
        self.assertFalse(self.check_action())

    def test_expired_request_is_rejected(self):
        with patch(
            "ai.action_executor.is_expired",
            return_value=True,
        ):
            self.assertFalse(self.check_action())

    def test_policy_denial_is_rejected(self):
        with patch(
            "ai.action_executor.get_safety_decision",
            return_value={
                "policy": "approval",
                "allowed": False,
                "requires_approval": True,
            },
        ):
            self.assertFalse(self.check_action())

    def test_action_not_requiring_approval_is_rejected(self):
        with patch(
            "ai.action_executor.get_safety_decision",
            return_value={
                "policy": "automatic",
                "allowed": True,
                "requires_approval": False,
            },
        ):
            self.assertFalse(self.check_action())

    def test_action_type_mismatch_is_rejected(self):
        changed_action = {
            **self.action,
            "action": "create_channel",
        }
        self.assertFalse(
            self.check_action(action=changed_action)
        )

    def test_payload_mismatch_is_rejected(self):
        changed_action = {
            **self.action,
            "new_name": "different-name",
        }
        self.assertFalse(
            self.check_action(action=changed_action)
        )

    def test_reason_mismatch_is_rejected(self):
        self.assertFalse(
            self.check_action(reason="Different reason")
        )

    def test_mutated_approved_snapshot_is_rejected(self):
        self.request.data["new_name"] = "tampered-name"
        self.assertFalse(self.check_action())

    def test_request_already_executing_is_rejected(self):
        self.request.executing = True
        self.assertFalse(self.check_action())

    def test_request_already_completed_is_rejected(self):
        self.request.completed = True
        self.assertFalse(self.check_action())


class TestApprovalExecutionLifecycle(unittest.TestCase):

    def setUp(self):
        approval_requests.clear()
        self.request_id = "lifecycle-test"

        create_approval_request(
            request_id=self.request_id,
            action="rename_channel",
            reason="Lifecycle test",
            data={
                "channel_id": 123,
                "new_name": "renamed",
            },
        )

    def tearDown(self):
        approval_requests.clear()

    def test_request_can_only_be_claimed_once(self):
        self.assertTrue(approve_request(self.request_id))

        action = {
            "action": "rename_channel",
            "channel_id": 123,
            "new_name": "renamed",
        }

        self.assertTrue(
            claim_approved_request(
                self.request_id,
                action,
                "Lifecycle test",
            )
        )

        self.assertFalse(
            claim_approved_request(
                self.request_id,
                action,
                "Lifecycle test",
            )
        )

    def test_modified_data_after_approval_is_rejected(self):
        self.assertTrue(approve_request(self.request_id))

        request = approval_requests[self.request_id]
        request.data["new_name"] = "tampered"

        action = {
            "action": "rename_channel",
            "channel_id": 123,
            "new_name": "tampered",
        }

        self.assertFalse(
            claim_approved_request(
                self.request_id,
                action,
                "Lifecycle test",
            )
        )

    def test_successful_execution_is_recorded(self):
        self.assertTrue(approve_request(self.request_id))

        action = {
            "action": "rename_channel",
            "channel_id": 123,
            "new_name": "renamed",
        }

        self.assertTrue(
            claim_approved_request(
                self.request_id,
                action,
                "Lifecycle test",
            )
        )

        self.assertTrue(
            complete_approval_request(
                self.request_id,
                success=True,
            )
        )

        request = approval_requests[self.request_id]
        self.assertEqual(request.status, "completed")
        self.assertTrue(request.execution_succeeded)

    def test_failed_execution_is_recorded(self):
        self.assertTrue(approve_request(self.request_id))

        action = {
            "action": "rename_channel",
            "channel_id": 123,
            "new_name": "renamed",
        }

        self.assertTrue(
            claim_approved_request(
                self.request_id,
                action,
                "Lifecycle test",
            )
        )

        self.assertTrue(
            complete_approval_request(
                self.request_id,
                success=False,
            )
        )

        request = approval_requests[self.request_id]
        self.assertEqual(request.status, "failed")
        self.assertFalse(request.execution_succeeded)

    def test_cancelled_request_cannot_be_claimed(self):
        from security.approval import cancel_request

        self.assertTrue(cancel_request(self.request_id))

        action = {
            "action": "rename_channel",
            "channel_id": 123,
            "new_name": "renamed",
        }

        self.assertFalse(
            claim_approved_request(
                self.request_id,
                action,
                "Lifecycle test",
            )
        )


if __name__ == "__main__":
    unittest.main()