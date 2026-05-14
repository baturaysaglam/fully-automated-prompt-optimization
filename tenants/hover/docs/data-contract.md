<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory

- `datasets/datasets/train.jsonl` — 150 cases (3-hop claims from HoVer)
- `datasets/datasets/val.jsonl` — 300 cases
- `datasets/datasets/test.jsonl` — 300 cases
- Built via `code/build_cases_jsonl.py` from HuggingFace `hover-nlp/hover`.

## Case Schema

```json
{
  "case_id": "hover_12345",
  "task_type": "claim_verification",
  "context": {"claim": "<claim text>"},
  "expected": {
    "supporting_titles": ["Title A", "Title B", "Title C"],
    "label": "SUPPORTED"
  },
  "metadata": {
    "source": "hover",
    "num_hops": 3
  }
}
```

## Check Expectations

- Scorer: `code/scorers/hover_scorer.py::Scorer`
- `composite_score`: 0 or 100 (binary — all gold titles found or not).
- `score_breakdown` keys: `recall`, `gold_titles`, `found_titles`, `missing_titles`.

## Dataset Update Procedure

- Re-run `python tenants/hover/code/build_cases_jsonl.py` to regenerate from HuggingFace.
