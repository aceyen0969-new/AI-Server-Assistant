import copy
import unittest
from unittest.mock import patch

import ai.health as health


class TestAIHealth(unittest.TestCase):

    def setUp(self):
        self.original_providers = copy.deepcopy(
            health.providers
        )

        for provider in health.providers.values():
            provider["status"] = "unknown"
            provider["available"] = False
            provider["retry_at"] = 0

    def tearDown(self):
        health.providers.clear()
        health.providers.update(self.original_providers)

    def test_unknown_provider_can_be_attempted(self):
        self.assertTrue(health.is_available("Groq"))

        self.assertEqual(
            health.providers["Groq"]["status"],
            "unknown",
        )

    def test_success_marks_provider_online(self):
        health.mark_success("Groq")

        self.assertTrue(health.is_available("Groq"))

        self.assertEqual(
            health.providers["Groq"]["status"],
            "online",
        )

        self.assertEqual(
            health.get_ai_status(),
            "online",
        )

    def test_failure_blocks_provider_during_cooldown(self):
        with patch.object(health.time, "time", return_value=1000):
            health.mark_failure("Groq", 30)

        with patch.object(health.time, "time", return_value=1010):
            self.assertFalse(health.is_available("Groq"))

            self.assertEqual(
                health.providers["Groq"]["status"],
                "offline",
            )

    def test_expired_cooldown_allows_retry(self):
        with patch.object(health.time, "time", return_value=1000):
            health.mark_failure("Groq", 30)

        with patch.object(health.time, "time", return_value=1030):
            self.assertTrue(health.is_available("Groq"))

            self.assertEqual(
                health.providers["Groq"]["status"],
                "unknown",
            )

            self.assertEqual(
                health.providers["Groq"]["retry_at"],
                0,
            )

    def test_status_check_resets_expired_cooldown(self):
        with patch.object(health.time, "time", return_value=1000):
            health.mark_failure("Groq", 30)

        with patch.object(health.time, "time", return_value=1030):
            statuses = health.get_status()

        self.assertEqual(
            statuses["Groq"]["status"],
            "unknown",
        )

        self.assertFalse(
            statuses["Groq"]["available"]
        )

    def test_unknown_provider_does_not_confirm_ai_online(self):
        self.assertEqual(
            health.get_ai_status(),
            "offline",
        )

    def test_unknown_provider_name_is_handled_safely(self):
        self.assertFalse(
            health.is_available("UnknownProvider")
        )

        health.mark_success("UnknownProvider")
        health.mark_failure("UnknownProvider", 30)

        self.assertNotIn(
            "UnknownProvider",
            health.providers,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)