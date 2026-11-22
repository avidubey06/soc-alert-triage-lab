# SOC Alert Triage Lab

A Python lab for investigating repeated failed logins followed by a successful login. It runs offline on synthetic authentication events.

## Run the lab

Requires Python 3.10 or newer. No external packages are needed.

```sh
python triage.py events.csv
```

The script groups events by account and source address. It reports a success preceded by at least three failures from that group within ten minutes. Each alert includes the timestamps of the matched failures and success.

## Sample incident report

| Time (UTC) | Evidence |
| --- | --- |
| 09:00–09:02 | Three failed sign-ins for `alex` from `192.0.2.10` |
| 09:04 | Successful sign-in for the same account and source |
| 09:05 | A separate account, `sam`, has one failed sign-in and does not meet the rule |

**Disposition** — Investigate the sign-in. Mistyped passwords could explain the pattern. Confirm whether the activity was expected, review MFA and device details, and look for unusual activity after the successful sign-in before deciding whether to escalate.

## Data and limitations

Input columns are `timestamp`, `account`, `source`, and `outcome`. Timestamps must include a timezone and outcomes are `failure` or `success`. The sample CSV is fictional. The rule can miss activity spread across accounts or source addresses and does not have device or MFA context.
