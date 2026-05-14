<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory
- `datasets/datasets/all.jsonl` — full 1000 cases from HuggingFace `AI4Sec/cti-bench` (subset `cti-rcm`).
- `datasets/datasets/dev.jsonl` — ~173 cases, stratified by CWE. Used for optimization and failure analysis.
- `datasets/datasets/test.jsonl` — ~827 cases, stratified by CWE + all rare-CWE cases. Used for final score reporting only.
- Built via `code/build_cases_jsonl.py --split` (seed=42, rare_threshold=3, dev_fraction=0.2).
- Rare CWEs (≤3 total cases) appear only in test to prevent overfitting during optimization.

## Case Schema
```json
{
  "case_id": "<row_index>",
  "task_type": "root_cause_mapping",
  "context": {"description": "<CVE description prefixed with 'CVE Description: '>"},
  "expected": {"cwe_id": "<CWE-NNN>"},
  "metadata": {"source": "AI4Sec/cti-bench", "subset": "cti-rcm"}
}
```

## Label Taxonomy
- Labels are CWE IDs in uppercase format: `CWE-<digits>` (e.g., `CWE-79`, `CWE-416`).
- Each case has exactly one ground-truth CWE ID.

## Check Expectations
- Scorer: `code/scorers/cti_rcm_scorer.py::Scorer`
- `composite_score`: 0 or 100 (exact match on extracted CWE ID).
- `score_breakdown` keys: `exact_match` (0 or 100), `answer_format` (100 = proper, 50 = improper, 0 = invalid).
- `answer_format_label`: string label for the extraction format ("proper", "improper", or "invalid").

## Dataset Update Procedure
- Re-run `python tenants/cti_rcm/code/build_cases_jsonl.py` to regenerate from HuggingFace via faith.
- Upload to GCS: `python -m hephaestus.cli customer-data push --tenant cti_rcm --scope derived`.
