from __future__ import annotations

import unittest

from garmin_training.swimming import aggregate_weekly_pool, analyze_pool_swim


class PoolSwimmingTests(unittest.TestCase):
    def test_pool_pace_uses_minute_per_hundred_meter_canonical_units(self) -> None:
        result = analyze_pool_swim(
            {
                "sport": "pool_swim",
                "distance_meters": 1000,
                "duration_seconds": 1500,
                "moving_time_seconds": 1200,
                "pool_length_meters": 25,
                "lengths": 40,
                "swolf": 42,
            }
        )

        self.assertEqual(150.0, result["pace_seconds_per_100m"])
        self.assertEqual(42, result["swolf"])

    def test_missing_sensor_data_remains_unavailable(self) -> None:
        result = analyze_pool_swim(
            {"sport": "pool_swim", "distance_meters": 100, "duration_seconds": 180}
        )

        self.assertIsNone(result["stroke_type"])
        self.assertIsNone(result["swolf"])
        self.assertIsNone(result["average_heart_rate"])

    def test_open_water_and_gps_data_are_not_analyzed(self) -> None:
        with self.assertRaises(ValueError):
            analyze_pool_swim(
                {
                    "sport": "open_water",
                    "distance_meters": 1000,
                    "duration_seconds": 1500,
                    "gps_track": "should-not-be-used",
                }
            )

    def test_weekly_aggregation_uses_pool_activities_only(self) -> None:
        result = aggregate_weekly_pool(
            [
                {"sport": "pool_swim", "distance_meters": 1000, "duration_seconds": 1500},
                {"sport": "pool_swim", "distance_meters": 500, "duration_seconds": 900},
                {"sport": "run", "distance_meters": 5000, "duration_seconds": 1800},
            ]
        )

        self.assertEqual({"distance_meters": 1500.0, "duration_seconds": 2400.0}, result)


if __name__ == "__main__":
    unittest.main()