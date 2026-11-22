"""Compare authentication detection settings on separate synthetic splits."""
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from random import Random

from triage import investigate


def dataset(seed):
    rng = Random(seed)
    scenarios = [
        ("typo", False, 1, 1, 30, False),
        ("reset_retries", False, 3, 5, 120, False),
        ("unrelated_old_failures", False, 3, 6, 1400, False),
        ("rapid_suspicious_login", True, 3, 7, 30, False),
        ("slow_suspicious_login", True, 4, 6, 540, False),
        ("distributed_sources", True, 4, 6, 30, True),
    ]
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for name, expected, minimum, maximum, gap, distributed in scenarios:
        for _ in range(40):
            failures = rng.randint(minimum, maximum)
            step = rng.randint(12, 25)
            rows = []
            for index in range(failures + 1):
                success = index == failures
                seconds = index * step + (gap + rng.randint(0, 120) if success else 0)
                rows.append({
                    "timestamp": (start + timedelta(seconds=seconds)).isoformat(),
                    "account": "lab-user",
                    "source": f"192.0.2.{10 + index if distributed else 10}",
                    "outcome": "success" if success else "failure",
                })
            rng.shuffle(rows)
            yield name, expected, rows


def evaluate(cases, threshold, minutes):
    outcomes = Counter()
    misses = Counter()
    for name, expected, rows in cases:
        found = bool(list(investigate(rows, threshold, timedelta(minutes=minutes))))
        outcomes[expected, found] += 1
        if expected != found:
            misses[name] += 1
    tp, fp, fn, tn = (outcomes[pair] for pair in
                      [(True, True), (False, True), (True, False), (False, False)])
    return {
        "threshold": threshold, "minutes": minutes, "tp": tp, "fp": fp,
        "fn": fn, "tn": tn, "precision": tp / (tp + fp) if tp + fp else 0,
        "recall": tp / (tp + fn), "f1": 2 * tp / (2 * tp + fp + fn),
        "errors_by_scenario": dict(misses),
    }


def main():
    tuning = list(dataset(11))
    holdout = list(dataset(29))
    grid = [evaluate(tuning, threshold, minutes)
            for threshold in (2, 3, 4, 5) for minutes in (5, 10, 20)]
    best = max(grid, key=lambda row: (row["f1"], row["precision"]))
    report = {
        "tuning_cases": len(tuning), "holdout_cases": len(holdout),
        "tuning_results": grid,
        "default_holdout": evaluate(holdout, 3, 10),
        "selected_holdout": evaluate(holdout, best["threshold"], best["minutes"]),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
