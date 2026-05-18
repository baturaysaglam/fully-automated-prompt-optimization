<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory

- `datasets/datasets/train.jsonl` — 121 cases (HuggingFace `livebench/math`, seed=0, first 33%)
- `datasets/datasets/val.jsonl` — 121 cases (33%-66%)
- `datasets/datasets/test.jsonl` — 126 cases (66%-100%)
- Built via `code/build_cases_jsonl.py`.

## Case Schema

```json
{
  "case_id": "livebench_math_0042",
  "task_type": "math",
  "context": {"question": "<problem text>"},
  "expected": {
    "question_d": {
      "question_id": "...",
      "task": "math_competitions",
      "subtask": "amc_2024",
      "category": "math",
      "turns": ["<problem text>"],
      "ground_truth": "C"
    }
  },
  "metadata": {
    "source": "livebench/math",
    "task": "math_competitions",
    "subtask": "amc_2024",
    "category": "math"
  }
}
```

## Label Taxonomy

- AMC/SMC: single letter A-E
- AIME: non-negative integer (0-999)
- IMO/USAMO: comma-separated integer sequence
- AMPS Hard: LaTeX symbolic expression

## Check Expectations

- Scorer: `code/scorers/livebench_math_scorer.py::Scorer`
- `composite_score`: 0-100 (binary for most tasks, fractional for olympiad).
- `score_breakdown` keys: `score`, `task`, `subtask`, `feedback`.

## Dataset Update Procedure

- Re-run `python tenants/livebench_math/code/build_cases_jsonl.py` to regenerate from HuggingFace.
- Upload to GCS: `python -m hephaestus.cli customer-data push --tenant livebench_math --scope derived`.
