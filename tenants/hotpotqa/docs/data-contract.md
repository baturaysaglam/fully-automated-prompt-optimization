<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Data Contract

## Dataset Inventory
- `datasets/datasets/train.jsonl` — 150-case training split (hard questions from HotpotQA fullwiki train).
- `datasets/datasets/val.jsonl` — 300-case validation split (hard questions from HotpotQA fullwiki train, held-out).
- `datasets/datasets/test.jsonl` — 300-case test split (HotpotQA fullwiki validation).
- Source: HuggingFace `hotpot_qa` `fullwiki` dataset, split via DSPy pipeline.

## Case Schema
- `case_id`: HotpotQA question ID (string).
- `task_type`: `"multihop_qa"`.
- `context.question`: the multi-hop question text.
- `expected.answer`: gold short answer string.
- `expected.answer_type`: `"bridge"` or `"comparison"`.
- `expected.supporting_facts`: list of `[title, sentence_index]` pairs.
- `metadata.level`: `"hard"`.
- `metadata.source`: `"hotpotqa-fullwiki"`.

## Label Taxonomy
- Answer types: bridge (entity-linking across documents) and comparison (comparing attributes).
- Difficulty levels: hard (all cases are hard after DSPy-style filtering).

## Check Expectations
- Scorer module: `tenants/hotpotqa/code/scorers/hotpotqa_scorer.py` with class `Scorer`.
- `score_breakdown` keys: `exact_match` (0 or 100) and `f1` (0-100).
- `composite_score` = exact_match (pure EM, matching GEPA's `answer_exact_match` metric).

## Dataset Update Procedure
- Re-run `code/build_cases_jsonl.py` to regenerate (use `--train-size`, `--val-size`, `--test-size` to adjust counts).
- Validate output loads as `EvalCase` list before committing.
