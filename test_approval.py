import unittest
import uuid
from unittest.mock import patch

import security.approval as approval


class TestApproval(unittest.TestCase):

    def setUp(self):
        self.original_requests = (
            approval.approval_requests.copy()
        )
        approval.approval_requests.clear()

        self.request_id = str(uuid.uuid4())

        approval.create_approval_request(
            request_id=self.request_id,
            action="rename_channel",
            target_id=123,
            target_name="general",
            reason="Test approval",
            data={
                "channel_id": 123,
                "new_name": "general-chat",
            },
        )

    def tearDown(self):
        approval.approval_requests.clear()
        approval.approval_requests.update(
            self.original_requests
        )

    def test_request_can_be_retrieved(self):
        request = approval.get_approval_request(
            self.request_id
        )

        self.assertIsNotNone(request)
        self.assertEqual(
            request.action,
            "rename_channel",
        )

    def test_request_can_be_approved_once(self):
        self.assertTrue(
            approval.approve_request(self.request_id)
        )
        self.assertFalse(
            approval.approve_request(self.request_id)
        )
        self.assertTrue(
            approval.is_approved(self.request_id)
        )

    def test_request_can_be_cancelled_once(self):
        self.assertTrue(
            approval.cancel_request(self.request_id)
        )
        self.assertFalse(
            approval.cancel_request(self.request_id)
        )
        self.assertTrue(
            approval.is_cancelled(self.request_id)
        )

    def test_cancelled_request_cannot_be_approved(self):
        approval.cancel_request(self.request_id)

        self.assertFalse(
            approval.approve_request(self.request_id)
        )
        self.assertFalse(
            approval.is_approved(self.request_id)
        )

    def test_approved_request_cannot_be_cancelled(self):
        approval.approve_request(self.request_id)

        self.assertFalse(
            approval.cancel_request(self.request_id)
        )
        self.assertTrue(
            approval.is_approved(self.request_id)
        )

    def test_missing_request_cannot_be_approved_or_cancelled(self):
        missing_id = str(uuid.uuid4())

        self.assertFalse(
            approval.approve_request(missing_id)
        )
        self.assertFalse(
            approval.cancel_request(missing_id)
        )
        self.assertIsNone(
            approval.get_approval_request(missing_id)
        )

    def test_request_expires_after_five_minutes(self):
        with patch.object(
            approval.time,
            "time",
            return_value=1000,
        ):
            request = approval.create_approval_request(
                request_id=str(uuid.uuid4()),
                action="rename_channel",
                expires_in=300,
            )

        with patch.object(
            approval.time,
            "time",
            return_value=1299,
        ):
            self.assertFalse(
                approval.is_expired(request.request_id)
            )

        with patch.object(
            approval.time,
            "time",
            return_value=1300,
        ):
            self.assertTrue(
                approval.is_expired(request.request_id)
            )
            self.assertFalse(
                approval.approve_request(request.request_id)
            )
            self.assertFalse(
                approval.cancel_request(request.request_id)
            )

    def test_custom_expiration_is_respected(self):
        request_id = str(uuid.uuid4())

        with patch.object(
            approval.time,
            "time",
            return_value=1000,
        ):
            approval.create_approval_request(
                request_id=request_id,
                action="rename_channel",
                expires_in=60,
            )

        with patch.object(
            approval.time,
            "time",
            return_value=1059,
        ):
            self.assertFalse(
                approval.is_expired(request_id)
            )

        with patch.object(
            approval.time,
            "time",
            return_value=1060,
        ):
            self.assertTrue(
                approval.is_expired(request_id)
            )

    def test_invalid_expiration_is_rejected(self):
        with self.assertRaises(ValueError):
            approval.create_approval_request(
                request_id=str(uuid.uuid4()),
                action="rename_channel",
                expires_in=0,
            )

        with self.assertRaises(ValueError):
            approval.create_approval_request(
                request_id=str(uuid.uuid4()),
                action="rename_channel",
                expires_in=-1,
            )

        with self.assertRaises(TypeError):
            approval.create_approval_request(
                request_id=str(uuid.uuid4()),
                action="rename_channel",
                expires_in="300",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)