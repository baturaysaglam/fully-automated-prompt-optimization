<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory
- `datasets/datasets/train.jsonl` — 111 cases (first 111 rows of `Columbia-NLP/PUPA/pupa_new` train).
- `datasets/datasets/val.jsonl` — 111 cases (rows 111–222).
- `datasets/datasets/test.jsonl` — 221 cases (rows 222–443).
- `datasets/datasets/splits.meta.json` — fingerprint + gepa-artifact git SHA.
- Splits are committed to git for byte-level lock with GEPA.

## Case Schema
- `case_id`: `"papillon-{train|val|test}-{idx}"`.
- `task_type`: `"privacy_utility"`.
- `context.user_query`: the user's private request (string).
- `expected.target_response`: gold reference response from PUPA.
- `expected.pii_str`: raw `||`-delimited PII string from the source.
- `expected.pii_units`: ordered, de-duplicated list of PII units (split + stripped).
- `metadata.source`: `"Columbia-NLP/PUPA/pupa_new"`.
- `metadata.split`: split name.
- `metadata.conversation_hash` / `metadata.predicted_category`: provenance back to PUPA.

## Label Taxonomy
- No categorical label. Each case is scored on two axes:
  - Leakage: fraction of `pii_units` that appear literally in the redacted request.
  - Quality: binary LLM-judge output (0 or 1) comparing the model's response to `target_response`.

## Check Expectations
- Scorer module: `tenants/papillon/code/scorers/papillon_scorer.py` with class `Scorer`.
- `score_breakdown` keys: `quality` (0 or 100), `leakage_rate` (0.0–1.0), `composite`.
- `composite_score` = `100 * (quality + (1 - leakage_rate)) / 2`.

## Dataset Update Procedure
- Re-run `code/build_cases_jsonl.py` to regenerate from cached HF PUPA data.
- The builder rewrites `splits.meta.json`; commit alongside the JSONLs.
- Do NOT hand-edit JSONL files — byte-level identity with the GEPA-author split is the guarantee we depend on.
