"""Evaluate a second, account-wide sign-in rule on synthetic cases."""
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from benchmarks.detection import dataset
from triage import investigate

WINDOW = timedelta(minutes=20)


def account_alerts(rows):
    failures = defaultdict(list)
    ordered = sorted(rows, key=lambda row: datetime.fromisoformat(row["timestamp"]))
    for row in ordered:
        account = row["account"]
        stamp = datetime.fromisoformat(row["timestamp"])
        recent = failures[account]
        if row["outcome"] == "failure":
            recent.append((stamp, row["source"]))
            continue
        window = [(time, source) for time, source in recent if stamp - time <= WINDOW]
        if len(window) >= 4 and len({source for _, source in window}) >= 2:
            yield account, row["timestamp"]
        recent.clear()


def new_cases():
    start = datetime(2026, 2, 1, tzinfo=timezone.utc)
    cases = [
        ("distributed_recovery", True, [10, 11, 12, 13, 14]),
        ("benign_laptop_phone_retries", False, [10, 11, 10, 11, 10]),
        ("single_source_incident", True, [10, 10, 10, 10, 10]),
        ("below_threshold", False, [10, 11, 12, 12]),
    ]
    for name, expected, sources in cases:
        rows = [
            dict(timestamp=(start + timedelta(seconds=30 * index)).isoformat(),
                 account="lab-user", source=f"192.0.2.{source}",
                 outcome="success" if index == len(sources) - 1 else "failure")
            for index, source in enumerate(sources)
        ]
        yield name, expected, rows


def evaluate(cases):
    counts = {name: Counter() for name in ("baseline", "combined")}
    annotations = {}
    for name, expected, rows in cases:
        baseline = {(alert["account"], alert["successful_login"]): {"account_source"}
                    for alert in investigate(rows, 4, WINDOW)}
        combined = {key: set(rules) for key, rules in baseline.items()}
        for key in account_alerts(rows):
            combined.setdefault(key, set()).add("account")
        for label, alerts in zip(counts, (baseline, combined)):
            count = counts[label]
            count[("tp" if expected else "fp") if alerts else ("fn" if expected else "tn")] += 1
            if alerts and name.startswith("distributed"):
                count["distributed_detected"] += 1
        annotations.setdefault(name, {
            "expected_alert": expected, "rows": rows,
            "combined_alerts": [dict(account=key[0], successful_login=key[1], rules=sorted(rules))
                                for key, rules in sorted(combined.items())],
        })
    metrics = {}
    for label, count in counts.items():
        tp, fp, fn = (count[key] for key in ("tp", "fp", "fn"))
        metrics[label] = dict(tp=tp, fp=fp, fn=fn, tn=count["tn"],
                              precision=tp / (tp + fp) if tp + fp else None,
                              recall=tp / (tp + fn) if tp + fn else None,
                              distributed_detected=count["distributed_detected"])
    return metrics, annotations


def main():
    regression, _ = evaluate(dataset(29))
    examples, annotations = evaluate(new_cases())
    print(json.dumps(dict(regression=regression, additional_sanity_cases=examples,
                          annotated_cases=annotations), indent=2))


if __name__ == "__main__":
    main()
