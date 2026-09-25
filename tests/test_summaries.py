from __future__ import annotations

import unittest

from garmin_training.summaries import summarize_activity


class ActivitySummaryTests(unittest.TestCase):
    def test_running_summary_is_deterministic_and_includes_available_metrics(self) -> None:
        activity = {
            "sport": "run",
            "duration_seconds": 600,
            "distance_meters": 2000,
            "calories": 400,
            "training_effect_aerobic": 2.5,
        }

        first = summarize_activity(activity)
        second = summarize_activity(activity)

        self.assertEqual(first, second)
        self.assertEqual("5:00 min/km", first["pace"])
        self.assertNotIn("max_heart_rate", first)

    def test_cycling_summary_uses_meters_per_second_for_speed_calculation(self) -> None:
        summary = summarize_activity(
            {"sport": "cycling", "duration_seconds": 3600, "distance_meters": 30000}
        )

        self.assertAlmostEqual(30.0, summary["speed_kmh"])

    def test_pool_summary_preserves_unavailable_metrics(self) -> None:
        summary = summarize_activity(
            {"sport": "pool_swim", "duration_seconds": 600, "distance_meters": 400}
        )

        self.assertEqual(150.0, summary["pace_seconds_per_100m"])
        self.assertIsNone(summary["swolf"])


if __name__ == "__main__":
    unittest.main()