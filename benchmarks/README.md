# Detection engineering benchmark

Compare 12 threshold and time-window combinations on 240 synthetic tuning cases. Select the setting by F1, breaking ties with precision, then compare it with the existing lab rule on 240 separately seeded holdout cases.

Run from the repository root with Python 3.10 or newer.

```sh
python -m benchmarks.detection
```

| Holdout setting | Precision | Recall | False positives | False negatives |
| --- | ---: | ---: | ---: | ---: |
| 3 failures in 10 minutes | 51.8% | 35.8% | 40 | 77 |
| 4 failures in 20 minutes | 78.3% | 60.0% | 20 | 48 |

The tuned rule recovered all 40 slow suspicious cases but missed eight rapid cases. Password-reset retries still produced 20 false positives. Both settings missed all 40 distributed-source cases because the parent lab groups by account and source. See the [full report](detection-report.json) for the tuning grid and scenario counts.

Each split draws from the same six scenario templates. The balanced classes and scripted timing help compare rules under repeatable conditions. These figures describe this dataset only.

# AI triage output evaluation

Evaluate structured alert summaries for severity agreement, unsupported claims, and coverage of required evidence. An output claim has three strings in order: evidence ID, field, and value. A claim only matches when all three agree with the case evidence.

```sh
python -m benchmarks.ai_evaluation benchmarks/fixtures/cases.json benchmarks/fixtures/grounded.json
python -m benchmarks.ai_evaluation benchmarks/fixtures/cases.json benchmarks/fixtures/flawed.json
```

| Handwritten candidate | Severity agreement | Unsupported claims | Required evidence recovered |
| --- | ---: | ---: | ---: |
| Grounded | 4/4 | 0/8 | 8/8 |
| Flawed | 3/4 | 1/7 | 6/8 |

The flawed fixture claims MFA was bypassed even though the record says its result was unknown. It also omits execution status in the quarantined-file case. The report names each affected case and claim.

To evaluate a model, give it only the case ID and evidence. Ask it to return an array with one object per case containing `id`, `severity` (low, medium, or high), and `claims`. Save the response as JSON and supply it as the second argument above. Keep the reference severity and required claims out of the model input. The published outputs are handwritten fixtures for exercising the evaluator. Exact matching is suitable for this structured format and does not assess free-text reasoning.
