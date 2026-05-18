<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- BM25 index built in `data/bm25/`.
- Datasets built via `code/build_cases_jsonl.py`.
- Baseline eval completed.

## Iteration Loop
1. Run baseline eval on val split.
2. Analyze train-split failures: which titles are consistently missed?
3. Improve query generation prompts to target missed entities.
4. Evaluate on val split.

## Stop Criteria
- Partial retrieval recall >= 60% on val split.
- Or: 3 consecutive iterations with no improvement.

## Scope Constraint
- Only modify prompt templates in `prompts/modules/*/variant-*.md`.
- Do NOT change retrieval parameters, model settings, or chain architecture.
