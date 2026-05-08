<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory
- `datasets/datasets/train.jsonl` — 121 training problems.
- `datasets/datasets/val.jsonl` — 121 validation problems.
- `datasets/datasets/test.jsonl` — 126 test problems.
- `datasets/datasets/splits.meta.json` — fingerprint + gepa-artifact git SHA (drift guard).
- Source: HuggingFace `livebench/math` (test split, 368 problems total), shuffled `random.Random(0)`, sequential 33/33/34 split, then `trim_dataset(seed=1)` (no-op here).

## Case Schema
- `case_id`: `"livebench-math-{train|val|test}-{idx}"`.
- `task_type`: `"livebench_math_cot"`.
- `context.question`: the math question (string, taken from `turns[0]`).
- `expected.answer`: the gold answer string (from the source row's `ground_truth`).
- `metadata.source`: `"livebench/math"`.
- `metadata.split`: split name.
- `metadata.task` / `metadata.subtask`: LiveBench task family (e.g., `math_comp` / `updated_amc_12a_2023`).
- `metadata.question_d`: a JSON-safe copy of the full source row. **Required** by the scorer because `calculate_livebench_score` dispatches on `question_d["task"]` / `question_d["subtask"]`.

## Label Taxonomy
- Binary correctness for AMC/SMC, AIME, and AMPS_Hard task families.
- Partial-credit (edit-distance) scoring for IMO/USAMO proof-rearrangement tasks.
- No label field beyond `expected.answer` — the gold is compared by GEPA's per-family utility functions.

## Check Expectations
- Scorer module: `tenants/livebench_math/code/scorers/livebench_math_scorer.py` with class `Scorer`.
- `score_breakdown` keys: `livebench_score` (0–100) and `scorer_ok` (0 or 100 if scorer executed without exception).
- `composite_score` = `livebench_score`.

## Dataset Update Procedure
- Re-run `code/build_cases_jsonl.py` to regenerate from cached HF `livebench/math` data.
- The builder rewrites `splits.meta.json`; commit alongside the JSONLs.
- Do NOT hand-edit JSONL files — byte-level identity with the GEPA-author split is the guarantee we depend on.
