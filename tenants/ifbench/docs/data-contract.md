<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory

- `datasets/datasets/val.jsonl` — 300 cases (rows 0-299 of IFBench_train.jsonl)
- `datasets/datasets/train.jsonl` — 150 cases (rows 300-449 of IFBench_train.jsonl)
- `datasets/datasets/test.jsonl` — 294 cases (all of IFBench_test.jsonl)
- Built via `code/build_cases_jsonl.py` from `source_artifacts/`.

## Case Schema

```json
{
  "case_id": "ifbench_train_0042",
  "task_type": "instruction_following",
  "context": {"prompt": "<instruction prompt text>"},
  "expected": {
    "instruction_id_list": ["count:word_count_range", "format:title_case"],
    "kwargs": [{"min_words": 50, "max_words": 100}, {}]
  },
  "metadata": {
    "source": "IFBench_train"
  }
}
```

## Check Expectations

- Scorer: `code/scorers/ifbench_scorer.py::Scorer`
- `composite_score`: 0-100 (fraction of instructions followed × 100).
- `score_breakdown` keys: `instruction_adherence`, `instructions_total`,
  `instructions_followed`, `feedback`.
- Multi-variant checking: 8 response variants tested per constraint.

## Dataset Update Procedure

- Re-run `python tenants/ifbench/code/build_cases_jsonl.py` to regenerate from source artifacts.
