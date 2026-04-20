<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory
- `datasets/datasets/test.jsonl` — small set of trivial yes/no questions for pipeline validation.

## Case Schema
```json
{
  "case_id": "<string>",
  "task_type": "yes_no_qa",
  "context": {"question": "<trivial yes/no question>"},
  "expected": {"answer": "yes | no"},
  "metadata": {}
}
```

## Label Taxonomy
- Two labels: `yes` and `no` (lowercase, exact strings).
- Each case has exactly one ground-truth answer.

## Check Expectations
- Scorer: `code/scorers/exact_match.py::Scorer`
- `composite_score`: 0 or 100 (case-insensitive exact match on stripped output).
- `score_breakdown` keys: `exact_match` (0 or 100).

## Dataset Update Procedure
- The dataset is intentionally static. If new cases are needed, add them manually to `test.jsonl` following the case schema above.
- Upload to GCS: `python -m hephaestus.cli customer-data push --tenant smoke_test --scope derived`.
