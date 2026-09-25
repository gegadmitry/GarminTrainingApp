from __future__ import annotations

import unittest

from garmin_training.running import analyze_running, format_pace, pace_seconds_per_kilometer


class RunningAnalysisTests(unittest.TestCase):
    def test_formats_canonical_pace_as_minutes_per_kilometer(self) -> None:
        self.assertEqual("5:30 min/km", format_pace(330, 1000))
        self.assertEqual(330, pace_seconds_per_kilometer(660, 2000))

    def test_rejects_zero_or_negative_distance(self) -> None:
        with self.assertRaises(ValueError):
            format_pace(330, 0)
        with self.assertRaises(ValueError):
            pace_seconds_per_kilometer(-1, 1000)

    def test_analyzes_laps_and_optional_metrics(self) -> None:
        result = analyze_running(
            {
                "duration_seconds": 600,
                "distance_meters": 2000,
                "average_heart_rate": 150,
                "cadence": 170,
                "elevation_gain_meters": 20,
            },
            laps=[
                {"duration_seconds": 300, "distance_meters": 1000},
                {"duration_seconds": 290, "distance_meters": 1000},
            ],
        )

        self.assertEqual("5:00 min/km", result["average_pace"])
        self.assertEqual(150, result["average_heart_rate"])
        self.assertEqual(290, result["best_pace_seconds_per_kilometer"])
        self.assertIn("pace_consistency_seconds", result)

    def test_missing_running_dynamics_do_not_fail(self) -> None:
        result = analyze_running({"duration_seconds": 600, "distance_meters": 2000})

        self.assertNotIn("cadence", result)
        self.assertNotIn("heart_rate_zones", result)


if __name__ == "__main__":
    unittest.main()