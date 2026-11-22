"""Score evidence-grounded triage output saved as JSON."""
import argparse
import json
from pathlib import Path

SEVERITIES = ("low", "medium", "high")


def index(rows):
    records = {}
    for row in rows:
        key = row["id"]
        if not isinstance(key, str) or not key or key in records:
            raise ValueError("case IDs must be unique nonempty strings")
        if row["severity"] not in SEVERITIES:
            raise ValueError(f"invalid severity for {key}")
        records[key] = row
    return records


def claims(rows):
    result = set()
    for row in rows:
        if (not isinstance(row, list) or len(row) != 3
                or any(not isinstance(item, str) or not item.strip() for item in row)):
            raise ValueError("claims must contain [evidence ID, field, value]")
        result.add(tuple(row))
    if len(result) != len(rows):
        raise ValueError("duplicate claims")
    return result


def evaluate(case_rows, candidate_rows):
    cases = index(case_rows)
    candidates = index(candidate_rows)
    if not cases or cases.keys() != candidates.keys():
        raise ValueError("candidates must cover exactly the nonempty set of case IDs")
    totals = dict(submitted=0, required=0, unsupported=0, missing=0, severity_matches=0)
    details = []
    for key, case in cases.items():
        candidate = candidates[key]
        evidence = claims(case["evidence"])
        required = claims(case["required"])
        if not required <= evidence:
            raise ValueError(f"invalid reference claims for {key}")
        submitted = claims(candidate["claims"])
        unsupported = submitted - evidence
        missing = required - submitted
        severity_matches = candidate["severity"] == case["severity"]
        totals["submitted"] += len(submitted)
        totals["required"] += len(required)
        totals["unsupported"] += len(unsupported)
        totals["missing"] += len(missing)
        totals["severity_matches"] += severity_matches
        details.append({"id": key, "severity_matches": severity_matches,
                        "unsupported": sorted(unsupported), "missing": sorted(missing)})
    return {
        "severity_accuracy": totals["severity_matches"] / len(cases),
        "unsupported_claim_rate": totals["unsupported"] / totals["submitted"]
        if totals["submitted"] else None,
        "required_claim_recall": 1 - totals["missing"] / totals["required"]
        if totals["required"] else None,
        "totals": totals,
        "cases": details,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path)
    parser.add_argument("candidates", type=Path)
    args = parser.parse_args()
    try:
        cases = json.loads(args.cases.read_text(encoding="utf-8"))
        candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
        result = evaluate(cases, candidates)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
