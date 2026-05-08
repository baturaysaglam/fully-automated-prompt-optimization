<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory
- `datasets/datasets/train.jsonl` — 150 training prompts.
- `datasets/datasets/val.jsonl` — 300 validation prompts.
- `datasets/datasets/test.jsonl` — 294 test prompts (the full IFBench test file; trim cap of 300 is above the source size so it is a no-op).
- `datasets/datasets/splits.meta.json` — fingerprint + gepa-artifact git SHA.
- Source: `gepa_artifact/benchmarks/IFBench/data/IFBench_{train,test}.jsonl` (the artifact ships these locally).

## Case Schema
- `case_id`: `"ifbench-{train|val|test}-{idx}"`.
- `task_type`: `"instruction_following"`.
- `context.prompt`: the user prompt with constraints embedded in natural language.
- `expected.instruction_id_list`: ordered list of `INSTRUCTION_DICT` keys (e.g., `["count:word_count_range"]`).
- `expected.kwargs`: ordered list of per-instruction kwargs dicts (aligned to `instruction_id_list`).
- `expected.key`: original `key` field from the IFBench source row.
- `metadata.source`: `"IFBench"`.
- `metadata.split`: split name.

## Label Taxonomy
- No categorical label. Each case has one or more instruction constraints that must all be satisfied for full credit.
- Partial credit: scorer reports the fraction of satisfied instructions.

## Check Expectations
- Scorer module: `tenants/ifbench/code/scorers/ifbench_scorer.py` with class `Scorer`.
- `score_breakdown` keys: `instruction_pass_rate` (0–100), `instructions_evaluated` (count), `scorer_ok` (100 if scored without exception, 0 otherwise).
- `composite_score` = `instruction_pass_rate`.

## Dataset Update Procedure
- Re-run `code/build_cases_jsonl.py` with `GEPA_ARTIFACT_PATH` set.
- The builder rewrites `splits.meta.json`; commit alongside the JSONLs.
- Do NOT hand-edit JSONL files — byte-level identity with the GEPA-author split is the guarantee we depend on.
