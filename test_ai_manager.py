import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import ai.manager as manager


class TestAIManager(unittest.TestCase):

    def run_async(self, coroutine):
        return asyncio.run(coroutine)

    def test_first_provider_success(self):
        async def scenario():
            with (
                patch.object(
                    manager,
                    "PROVIDERS",
                    [("Groq", AsyncMock(return_value="Hello"))],
                ),
                patch.object(manager, "is_available", return_value=True),
                patch.object(manager, "mark_success") as success,
                patch.object(manager, "mark_failure") as failure,
            ):
                result = await manager.ask_ai("test")

                self.assertEqual(
                    result,
                    {
                        "answer": "Hello",
                        "provider": "Groq",
                    },
                )
                success.assert_called_once_with("Groq")
                failure.assert_not_called()

        self.run_async(scenario())

    def test_falls_back_after_provider_failure(self):
        async def scenario():
            groq = AsyncMock(
                side_effect=RuntimeError("simulated failure")
            )
            gemini = AsyncMock(return_value="Gemini response")

            with (
                patch.object(
                    manager,
                    "PROVIDERS",
                    [
                        ("Groq", groq),
                        ("Gemini", gemini),
                    ],
                ),
                patch.object(manager, "is_available", return_value=True),
                patch.object(manager, "mark_success") as success,
                patch.object(manager, "mark_failure") as failure,
            ):
                result = await manager.ask_ai("test")

                self.assertEqual(
                    result["answer"],
                    "Gemini response",
                )
                self.assertEqual(
                    result["provider"],
                    "Gemini",
                )
                failure.assert_called_once_with("Groq", 30)
                success.assert_called_once_with("Gemini")

        self.run_async(scenario())

    def test_returns_failure_when_all_providers_fail(self):
        async def scenario():
            groq = AsyncMock(
                side_effect=RuntimeError("Groq failed")
            )
            gemini = AsyncMock(
                side_effect=RuntimeError("Gemini failed")
            )

            with (
                patch.object(
                    manager,
                    "PROVIDERS",
                    [
                        ("Groq", groq),
                        ("Gemini", gemini),
                    ],
                ),
                patch.object(manager, "is_available", return_value=True),
                patch.object(manager, "mark_failure"),
            ):
                result = await manager.ask_ai("test")

                self.assertIsNone(result["answer"])
                self.assertIsNone(result["provider"])
                self.assertEqual(len(result["errors"]), 2)

        self.run_async(scenario())

    def test_skips_unavailable_provider(self):
        async def scenario():
            groq = AsyncMock(return_value="Should not run")
            gemini = AsyncMock(return_value="Gemini response")

            def availability(provider_name):
                return provider_name == "Gemini"

            with (
                patch.object(
                    manager,
                    "PROVIDERS",
                    [
                        ("Groq", groq),
                        ("Gemini", gemini),
                    ],
                ),
                patch.object(
                    manager,
                    "is_available",
                    side_effect=availability,
                ),
                patch.object(manager, "mark_success"),
            ):
                result = await manager.ask_ai("test")

                groq.assert_not_awaited()
                gemini.assert_awaited_once()

                self.assertEqual(
                    result["provider"],
                    "Gemini",
                )

        self.run_async(scenario())


if __name__ == "__main__":
    unittest.main(verbosity=2)