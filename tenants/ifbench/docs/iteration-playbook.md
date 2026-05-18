<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Datasets built via `code/build_cases_jsonl.py`.
- NLTK punkt_tab downloaded (auto on first scorer use).
- Baseline eval completed.

## Iteration Loop
1. Run baseline eval on val split.
2. Analyze train-split failures by instruction type.
3. Create new prompt variants targeting common failure patterns.
4. Evaluate on val split, then test split.

## Data Hygiene

| Split | File | Access Level |
|-------|------|-------------|
| **Train** | `train.jsonl` (150 cases) | **Full access.** |
| **Val** | `val.jsonl` (300 cases) | **Aggregate scores only.** |
| **Test** | `test.jsonl` (294 cases) | **Aggregate scores only.** Final confirmation. |

**Important**: Val and test use different instruction categories. Optimizing for val
may not directly improve test scores.

## Fixed Experimental Parameters

Immutable for the duration of this study (GEPA comparison fairness):
- `temperature`: 1.0
- `top_p`: 0.95
- `model`: as set in the baseline config (must not change within an optimization run)
- `max_tokens`: 16000

These must not be modified by any agent or optimization process. See `docs/processes/prompt-iteration-loop.md` § Experimental Constants.

## Budget
- **30 variant budget** per module (generate and verify).
- **Prompt-only optimization** — only modify prompt text.

## Stop Criteria
- Instruction adherence >= 55.5% on the test split.
- Or: variant budget exhausted.
- Or: 3 consecutive iterations with no improvement.

## Regression Prevention
- Run full chain eval on the validation split after each prompt change.
- Compare instruction adherence against previous best before accepting a new variant.

## Lessons Logging
- Record in `docs/change-log.md`.
