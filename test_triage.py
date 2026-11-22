import csv
import unittest
from pathlib import Path

from triage import investigate


def sequence(minutes, sources=None):
    sources = sources or ["192.0.2.10"] * len(minutes)
    return [
        {
            "timestamp": f"2026-01-01T09:{minute:02}:00+00:00",
            "account": "alex",
            "source": source,
            "outcome": "success" if index == len(minutes) - 1 else "failure",
        }
        for index, (minute, source) in enumerate(zip(minutes, sources))
    ]


class InvestigationTests(unittest.TestCase):
    def test_sample_file(self):
        with Path(__file__).with_name("events.csv").open(newline="", encoding="utf-8") as file:
            alerts = list(investigate(csv.DictReader(file)))
        self.assertEqual([alert["account"] for alert in alerts], ["alex"])
        self.assertEqual(len(alerts[0]["failures"]), 3)
        self.assertEqual(alerts[0]["successful_login"], "2026-01-01T09:04:00+00:00")

    def test_exact_window_boundary(self):
        self.assertEqual(len(list(investigate(sequence([0, 1, 2, 10])))), 1)

    def test_expired_failure(self):
        self.assertEqual(list(investigate(sequence([0, 1, 2, 11]))), [])

    def test_different_source(self):
        sources = ["192.0.2.10", "192.0.2.10", "192.0.2.11", "192.0.2.10"]
        self.assertEqual(list(investigate(sequence([0, 1, 2, 4], sources))), [])

    def test_success_resets_the_failure_count(self):
        events = sequence([0, 1, 2, 4])
        events.extend(sequence([5, 6]))
        self.assertEqual(len(list(investigate(reversed(events)))), 1)


if __name__ == "__main__":
    unittest.main()
