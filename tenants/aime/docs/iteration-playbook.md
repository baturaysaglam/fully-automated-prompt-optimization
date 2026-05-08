<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Global references:
  - `docs/processes/prompt-iteration-loop.md`
- Dataset present at `datasets/datasets/{train,val,test}.jsonl` (committed to git; rebuild via `code/build_cases_jsonl.py`).
- Baseline chain eval completed with results in `evals/tmp/`.

## Iteration Loop
1. Follow the global iteration loop from `docs/processes/prompt-iteration-loop.md`.
2. Optimize the `solve` prompt over the training split (`train.jsonl`, 45 cases). Follow Data Hygiene rules below for what analysis is allowed per split.
3. Evaluate on the validation split (`val.jsonl`, 45 cases) after each change. Only check aggregate scores (`exact_match`, `parse_ok`) — do not inspect individual val cases.
4. Iterate until tenant success criteria are met.

## Data Hygiene

These rules prevent overfitting by separating prompt-design data from evaluation data.

| Split | File | Access Level |
|-------|------|-------------|
| **Train** | `train.jsonl` (45 cases) | **Full access.** Inspect problems, gold answers, model outputs, and failure patterns. |
| **Val** | `val.jsonl` (45 cases) | **Aggregate scores only.** Check EM and parse rate totals. **Never** inspect individual cases. |
| **Test** | `test.jsonl` (150) | **Aggregate scores only.** Run once at the end for final confirmation. |

## Stop Criteria
- Reach target `exact_match` on val that matches or beats the GEPA paper's reported `AIMEBench` baseline.

## Regression Prevention
- Run full chain eval on val after each prompt change.
- Compare aggregate EM and parse_ok against previous best before accepting a new variant.

## Chain-Level Optimization Scope

The optimization agent reads this section to determine allowed optimization levels.

- **Structural changes**: NOT in-scope. Chain is fixed at 1 node (`chains/cot.py`). No retry/verification/self-consistency.
- **Parameter changes**: NOT in-scope. Model settings (`temperature`, `top_p`, `model`, `max_tokens`) are fixed to match GEPA's fairness envelope.
- **Prompt changes**: In-scope. Only modify `prompts/modules/solve/variant-*.md`.

## Lessons Logging
- Record iteration outcomes in `docs/change-log.md`.
