# SOC Alert Triage Lab

Would three failed sign-ins followed by a success be enough to escalate? This small Python lab turns a synthetic authentication log into a timeline for that decision.

## Case review

| Time (UTC) | What the log shows |
| --- | --- |
| 09:00–09:02 | Three failed sign-ins for `alex` from `192.0.2.10` |
| 09:04 | A successful sign-in for the same account and source |
| 09:05–09:10 | Separate account `sam` fails once and then signs in successfully |

**Decision:** Keep the alert open for review. The timing matches the rule, but the same sequence could come from password typos. The dataset has no MFA, device, or post-login events. In a real investigation, those records would help determine whether the successful sign-in was expected.

## Reproduce the result

Run with Python 3.10 or later. No packages or accounts are required.

```sh
python triage.py events.csv
python -m unittest -v
```

The sample produces one alert for `alex`, with the three failure timestamps and the success at 09:04 UTC. Five tests check the sample, the ten-minute boundary, expired failures, separate source addresses, and the reset after a successful sign-in.

## How the rule works

The script orders events by timestamp and tracks failures per account and source. At a successful sign-in, it checks whether at least three failures occurred in the preceding ten minutes, including the boundary. The success clears that group's failure history. This approach can miss activity distributed across accounts or source addresses.

The CSV uses fictional events. To try your own synthetic scenario, supply the columns `timestamp`, `account`, `source`, and `outcome`. Use timestamps with a timezone and either `failure` or `success` as the outcome.
