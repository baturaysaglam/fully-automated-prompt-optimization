<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory
- `datasets/datasets/train.jsonl` — 45-case training split (half of AI-MO/aimo-validation-aime, shuffled with seed=0).
- `datasets/datasets/val.jsonl` — 45-case validation split (other half of AI-MO/aimo-validation-aime).
- `datasets/datasets/test.jsonl` — 150-case test split (MathArena/aime_2025 replicated 5x, matching GEPA's `AIMEBench`).
- `datasets/datasets/splits.meta.json` — fingerprint + gepa-artifact git SHA (drift guard).
- Splits are committed to git for byte-level lock with GEPA; rebuild via `code/build_cases_jsonl.py`.

## Case Schema
- `case_id`: `"aime-{train|val|test}-{idx}"` (stringified integer index within split).
- `task_type`: `"math_cot"`.
- `context.problem`: the competition problem statement (string).
- `expected.answer`: the gold answer as a numeric string (integer, 0-999).
- `expected.solution`: optional full solution text (blank for test split).
- `metadata.source`: `"AI-MO/aimo-validation-aime"` (train/val) or `"MathArena/aime_2025"` (test).
- `metadata.split`: the split name.
- `metadata.original_id` / `metadata.original_problem_idx`: provenance back to the HF source.

## Label Taxonomy
- Single label per case: an integer answer.
- No category taxonomy — all cases are AIME competition problems.

## Check Expectations
- Scorer module: `tenants/aime/code/scorers/aime_scorer.py` with class `Scorer`.
- `score_breakdown` keys: `exact_match` (0 or 100) and `parse_ok` (0 or 100).
- `composite_score` = `exact_match` (pure integer EM, matching GEPA's `AIMEBench` metric).

## Dataset Update Procedure
- Re-run `code/build_cases_jsonl.py` to regenerate from cached HF datasets.
- The builder rewrites `splits.meta.json`; commit alongside the JSONLs.
- Do NOT hand-edit JSONL files — byte-level identity with the GEPA-author split is the guarantee we depend on.
