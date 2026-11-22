"""Find repeated failed logins followed by a successful login."""
import argparse
import csv
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path


def investigate(rows, threshold=3, window=timedelta(minutes=10)):
    events = []
    for row in rows:
        timestamp = datetime.fromisoformat(row["timestamp"])
        if timestamp.utcoffset() is None:
            raise ValueError("timestamps must include a timezone")
        if row["outcome"] not in {"failure", "success"}:
            raise ValueError("outcome must be failure or success")
        events.append((timestamp, row))

    failures = defaultdict(deque)
    for timestamp, row in sorted(events, key=lambda event: event[0]):
        account = row["account"]
        source = row["source"]
        recent = failures[account, source]
        while recent and timestamp - recent[0] > window:
            recent.popleft()
        if row["outcome"] == "failure":
            recent.append(timestamp)
            continue
        if len(recent) >= threshold:
            yield {
                "account": account,
                "source": source,
                "failures": [attempt.isoformat() for attempt in recent],
                "successful_login": timestamp.isoformat(),
            }
        recent.clear()


def main():
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="Authentication events CSV")
    args = parser.parse_args()
    try:
        with args.events.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            required = {"timestamp", "account", "source", "outcome"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("CSV must include timestamp, account, source, and outcome")
            alerts = list(investigate(reader))
    except (OSError, ValueError, TypeError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(json.dumps(alerts, indent=2))


if __name__ == "__main__":
    main()
