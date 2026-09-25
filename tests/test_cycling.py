from __future__ import annotations

import unittest

from garmin_training.cycling import analyze_cycling


class CyclingAnalysisTests(unittest.TestCase):
    def test_speed_and_common_metrics_are_reported_in_cycling_units(self) -> None:
        result = analyze_cycling(
            {
                "duration_seconds": 3600,
                "distance_meters": 30000,
                "elevation_gain_meters": 200,
                "cadence_rpm": 85,
                "average_heart_rate": 145,
            },
            samples=[
                {"speed_meters_per_second": 8},
                {"speed_meters_per_second": 9},
            ],
        )

        self.assertAlmostEqual(30.0, result["speed_kmh"])
        self.assertEqual(85, result["cadence_rpm"])
        self.assertIn("speed_consistency_mps", result)

    def test_power_metrics_require_valid_power_data(self) -> None:
        with_power = analyze_cycling(
            {"duration_seconds": 60, "distance_meters": 500, "average_power_watts": 200}
        )
        without_power = analyze_cycling({"duration_seconds": 60, "distance_meters": 500})

        self.assertTrue(with_power["power_available"])
        self.assertEqual(200, with_power["average_power_watts"])
        self.assertFalse(without_power["power_available"])
        self.assertNotIn("average_power_watts", without_power)

    def test_invalid_power_is_not_fabricated(self) -> None:
        result = analyze_cycling(
            {"duration_seconds": 60, "distance_meters": 500},
            samples=[{"power_watts": -1}],
        )

        self.assertFalse(result["power_available"])


if __name__ == "__main__":
    unittest.main()