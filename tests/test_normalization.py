from __future__ import annotations

import unittest

from garmin_training.normalization import normalize_activity


class NormalizationTests(unittest.TestCase):
    def test_running_values_are_canonical_and_source_is_preserved(self) -> None:
        source = {
            "garmin_activity_id": "run-1",
            "activity_type": "running",
            "duration_seconds": 600,
            "distance_meters": 2000,
            "start_time_utc": "2026-09-25T08:00:00Z",
        }

        normalized = normalize_activity(source, "garmin", "parser-1", "2026-09-25T09:00:00Z")

        self.assertEqual("run", normalized["sport"])
        self.assertEqual(300, normalized["pace_seconds_per_kilometer"])
        self.assertEqual(source, normalized["source_values"])
        self.assertEqual("parser-1", normalized["provenance"]["parser_version"])

    def test_cycling_speed_from_kmh_is_stored_as_meters_per_second(self) -> None:
        normalized = normalize_activity(
            {
                "activity_type": "cycling",
                "duration_seconds": 3600,
                "distance_meters": 30000,
                "average_speed_kmh": 30,
            },
            "garmin",
            "parser-1",
            "2026-09-25T09:00:00Z",
        )

        self.assertEqual(30 / 3.6, normalized["speed_meters_per_second"])

    def test_unknown_and_missing_optional_fields_remain_explicit(self) -> None:
        normalized = normalize_activity(
            {"duration_seconds": 60, "distance_meters": None},
            "garmin",
            "parser-1",
            "2026-09-25T09:00:00Z",
        )

        self.assertEqual("unknown", normalized["sport"])
        self.assertIsNone(normalized["distance_meters"])
        self.assertNotIn("pace_seconds_per_kilometer", normalized)

    def test_negative_measurements_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_activity(
                {"duration_seconds": -1, "distance_meters": 10},
                "garmin",
                "parser-1",
            )


if __name__ == "__main__":
    unittest.main()