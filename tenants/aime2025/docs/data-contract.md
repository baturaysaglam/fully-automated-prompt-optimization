<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory

- `datasets/datasets/train.jsonl` — 90 cases from AIME 2022-2024 (HuggingFace `AI-MO/aimo-validation-aime`)
- `datasets/datasets/test.jsonl` — 30 cases from AIME 2025 (HuggingFace `yentinglin/aime_2025`)
- Built via `code/build_cases_jsonl.py`.

## Case Schema

```json
{
  "case_id": "aime_2024_I_01",
  "task_type": "math_competition",
  "context": {"problem": "<LaTeX problem statement>"},
  "expected": {"answer": "70"},
  "metadata": {
    "source": "<hf_dataset_id>",
    "year": 2024,
    "exam": "I",
    "problem_number": 1
  }
}
```

## Label Taxonomy

- Answers are non-negative integers in [0, 999], stored as strings.
- Each case has exactly one ground-truth answer.

## Check Expectations

- Scorer: `code/scorers/aime_scorer.py::Scorer`
- `composite_score`: 0 or 100 (exact match or LLM equivalence).
- `score_breakdown` keys: `exact_match` (0 or 100), `llm_equiv` (0 or 100).
- Optional `predicted_answer` in breakdown when scoring fails.

## Dataset Update Procedure

- Re-run `python tenants/aime2025/code/build_cases_jsonl.py` to regenerate from HuggingFace.
- Upload to GCS: `python -m hephaestus.cli customer-data push --tenant aime2025 --scope derived`.
