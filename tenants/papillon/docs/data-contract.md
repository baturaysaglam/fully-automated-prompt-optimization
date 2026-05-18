<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory

- `datasets/datasets/train.jsonl` — 111 cases (sequential split from PUPA)
- `datasets/datasets/val.jsonl` — 111 cases
- `datasets/datasets/test.jsonl` — 221 cases
- Built via `code/build_cases_jsonl.py` from HuggingFace `Columbia-NLP/PUPA`.

## Case Schema

```json
{
  "case_id": "papillon_0042",
  "task_type": "privacy_preserving",
  "context": {
    "query": "<query with PII>",
    "pii_str": "John Smith||123 Main St||555-0100"
  },
  "expected": {
    "target_response": "<gold response>",
    "pii_str": "John Smith||123 Main St||555-0100"
  },
  "metadata": {
    "source": "Columbia-NLP/PUPA",
    "category": "personal_finance"
  }
}
```

## Label Taxonomy
- PII types: names, addresses, phone numbers, emails, SSNs, dates of birth.
- Categories: personal_finance, healthcare, legal, employment.
- Quality labels: binary pass/fail from LLM judge comparison.

## Check Expectations

- Scorer: `code/scorers/papillon_scorer.py::Scorer`
- `composite_score`: 0-100, formula: `(quality + privacy) / 2 × 100`
- `score_breakdown` keys: `quality`, `privacy`, `leakage_fraction`, `quality_passed`.
- Scorer uses `score_pipeline_case` (needs step_outputs for leakage check).

## Dataset Update Procedure

- Re-run `python tenants/papillon/code/build_cases_jsonl.py` to regenerate.
