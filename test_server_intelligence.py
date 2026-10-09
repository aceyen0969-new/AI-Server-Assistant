import unittest
from types import SimpleNamespace

from analytics.intelligence import (
    analyze_server_structure,
    build_server_snapshot,
    detect_structure_issues,
)


class ServerIntelligenceTests(unittest.TestCase):

    def make_channel(
        self,
        channel_id,
        name,
        channel_type="text",
        category_id=None,
    ):
        return SimpleNamespace(
            id=channel_id,
            name=name,
            type=channel_type,
            category_id=category_id,
        )

    def make_category(
        self,
        category_id,
        name,
        channels=None,
    ):
        return SimpleNamespace(
            id=category_id,
            name=name,
            channels=channels or [],
        )

    def make_guild(self, channels):
        return SimpleNamespace(
            id=12345,
            name="Test Server",
            channels=channels,
        )

    def test_builds_server_snapshot(self):
        category = self.make_category(
            100,
            "Community",
        )

        channel = self.make_channel(
            200,
            "general",
            category_id=100,
        )

        category.channels.append(channel)

        guild = self.make_guild([
            category,
            channel,
        ])

        snapshot = build_server_snapshot(guild)

        self.assertEqual(snapshot["guild_id"], 12345)
        self.assertEqual(snapshot["guild_name"], "Test Server")
        self.assertEqual(snapshot["channel_count"], 1)
        self.assertEqual(snapshot["category_count"], 1)
        self.assertEqual(snapshot["channels"][0]["name"], "general")
        self.assertTrue(snapshot["channels"][0]["has_category"])

    def test_detects_empty_category(self):
        snapshot = {
            "channels": [],
            "categories": [
                {
                    "id": 100,
                    "name": "Unused",
                    "channel_count": 0,
                }
            ],
        }

        findings = detect_structure_issues(snapshot)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["code"], "empty_category")

    def test_detects_uncategorized_channel(self):
        snapshot = {
            "channels": [
                {
                    "id": 200,
                    "name": "general",
                    "type": "text",
                    "category_id": None,
                }
            ],
            "categories": [],
        }

        findings = detect_structure_issues(snapshot)

        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0]["code"],
            "uncategorized_channel",
        )

    def test_detects_duplicate_names_case_insensitively(self):
        snapshot = {
            "channels": [
                {
                    "id": 200,
                    "name": "general",
                    "type": "text",
                    "category_id": 100,
                },
                {
                    "id": 201,
                    "name": "General",
                    "type": "text",
                    "category_id": 100,
                },
            ],
            "categories": [],
        }

        findings = detect_structure_issues(snapshot)

        duplicate_findings = [
            finding
            for finding in findings
            if finding["code"] == "possible_duplicate_channel_name"
        ]

        self.assertEqual(len(duplicate_findings), 1)
        self.assertEqual(
            len(duplicate_findings[0]["evidence"]["channels"]),
            2,
        )

    def test_does_not_flag_different_channel_types_as_duplicates(self):
        snapshot = {
            "channels": [
                {
                    "id": 200,
                    "name": "general",
                    "type": "text",
                    "category_id": 100,
                },
                {
                    "id": 201,
                    "name": "general",
                    "type": "voice",
                    "category_id": 100,
                },
            ],
            "categories": [],
        }

        findings = detect_structure_issues(snapshot)

        duplicate_findings = [
            finding
            for finding in findings
            if finding["code"] == "possible_duplicate_channel_name"
        ]

        self.assertEqual(duplicate_findings, [])

    def test_clean_server_has_no_findings(self):
        category = self.make_category(
            100,
            "Community",
        )

        channel = self.make_channel(
            200,
            "general",
            category_id=100,
        )

        category.channels.append(channel)

        guild = self.make_guild([
            category,
            channel,
        ])

        result = analyze_server_structure(guild)

        self.assertEqual(result["finding_count"], 0)
        self.assertEqual(result["findings"], [])

    def test_analysis_does_not_modify_guild(self):
        category = self.make_category(
            100,
            "Community",
        )

        channel = self.make_channel(
            200,
            "general",
            category_id=100,
        )

        category.channels.append(channel)

        guild = self.make_guild([
            category,
            channel,
        ])

        original_names = [
            item.name
            for item in guild.channels
        ]

        analyze_server_structure(guild)

        current_names = [
            item.name
            for item in guild.channels
        ]

        self.assertEqual(current_names, original_names)

    def test_rejects_invalid_snapshot(self):
        with self.assertRaises(ValueError):
            detect_structure_issues(None)


if __name__ == "__main__":
    unittest.main()