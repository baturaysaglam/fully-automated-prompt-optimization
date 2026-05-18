<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Datasets built via `code/build_cases_jsonl.py`.
- Baseline eval completed on val split.
- OPENAI_API_KEY set in environment.

## Iteration Loop
1. Run baseline eval on val split to establish starting accuracy.
2. Analyze train-split failures to identify prompt improvement opportunities.
3. Create new variant in `prompts/variants/variant-NNN.md`.
4. Evaluate on val split. Only accept changes showing consistent improvement.

## Data Hygiene

| Split | File | Access Level |
|-------|------|-------------|
| **Train** | `train.jsonl` (121 cases) | **Full access.** Inspect individual cases for failure analysis. |
| **Val** | `val.jsonl` (121 cases) | **Aggregate scores only.** Check composite score totals. |
| **Test** | `test.jsonl` (126 cases) | **Aggregate scores only.** Run once at the end. |

## Fixed Experimental Parameters

Immutable for the duration of this study (GEPA comparison fairness):
- `temperature`: 1.0
- `top_p`: 0.95
- `model`: gpt-4.1-mini
- `max_tokens`: 16000

These must not be modified by any agent or optimization process. See `docs/processes/prompt-iteration-loop.md` § Experimental Constants.

## Budget
- **30 variant budget** — maximum 30 prompt variants total.
- **Prompt-only optimization** — only modify prompt text in `prompts/variants/`.

## Stop Criteria
- Composite score >= 64% on the validation split.
- Or: variant budget exhausted (30 variants).
- Or: 3 consecutive iterations with no improvement.

## Regression Prevention
- Always evaluate on val split after each change.
- Track all variant scores in change-log.

## Lessons Logging
- Record insights in `docs/change-log.md` with date, variant, and score delta.
