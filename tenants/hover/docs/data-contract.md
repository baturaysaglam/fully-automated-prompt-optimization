<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory
- `datasets/datasets/train.jsonl` — 150 training claims.
- `datasets/datasets/val.jsonl` — 300 validation claims.
- `datasets/datasets/test.jsonl` — 300 test claims.
- `datasets/datasets/splits.meta.json` — fingerprint + gepa-artifact git SHA (drift guard).
- All cases are filtered to exactly 3 unique supporting-fact documents.
- Splits are committed to git for byte-level lock with GEPA.

## Case Schema
- `case_id`: `"hover-{train|val|test}-{idx}"`.
- `task_type`: `"claim_verification_retrieval"`.
- `context.claim`: the natural-language claim to verify (string).
- `expected.supporting_facts`: list of `{"key": "<Wikipedia title>", "value": <sentence_id>}`.
- `expected.label`: `"SUPPORTED"` or `"NOT_SUPPORTED"`.
- `expected.label_raw`: raw integer label from HF source (0 or 1).
- `metadata.source`: `"hover"`.
- `metadata.split`: split name.
- `metadata.original_id` / `metadata.original_uid`: provenance back to the HF source.

## Label Taxonomy
- Claim verdict labels: `SUPPORTED` (raw=0) or `NOT_SUPPORTED` (raw=1).
- Note: GEPA's `hoverBench` metric is purely retrieval-based (title-set subset) and does NOT use the verdict label. The label is preserved in `expected.label` for future label-based scorers but is currently unused by the scorer.

## Check Expectations
- Scorer module: `tenants/hover/code/scorers/hover_scorer.py` with class `Scorer`.
- `score_breakdown` keys: `retrieval_subset` (0 or 100), `gold_titles_found`, `gold_titles_total`, `title_recall` (0–100).
- `composite_score` = `retrieval_subset` (100 iff all 3 gold titles found across retrieve_hop1/2/3).

## Dataset Update Procedure
- Re-run `code/build_cases_jsonl.py` to regenerate from cached HF `hover` data.
- The builder rewrites `splits.meta.json`; commit alongside the JSONLs.
- Do NOT hand-edit JSONL files — byte-level identity with the GEPA-author split is the guarantee we depend on.
