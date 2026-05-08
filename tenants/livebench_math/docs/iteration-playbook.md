<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Global references:
  - `docs/processes/prompt-iteration-loop.md`
- Dataset present at `datasets/datasets/{train,val,test}.jsonl`.
- `GEPA_ARTIFACT_PATH` exported so the scorer can import `livebenchmath_utils.metric`.
- Baseline chain eval completed.

## Iteration Loop
1. Follow the global iteration loop from `docs/processes/prompt-iteration-loop.md`.
2. Optimize the `solve` prompt over train (`train.jsonl`, 121 cases).
3. Evaluate on val (`val.jsonl`, 121 cases). Only check aggregate scores.
4. Iterate until success criteria are met.

## Data Hygiene

| Split | File | Access Level |
|-------|------|-------------|
| **Train** | `train.jsonl` (121 cases) | **Full access.** Inspect questions, ground_truth, model outputs. |
| **Val** | `val.jsonl` (121 cases) | **Aggregate scores only.** |
| **Test** | `test.jsonl` (126 cases) | **Aggregate scores only. Run once at the end.** |

## Stop Criteria
- Reach target `livebench_score` on val matching/beating GEPA's reported `LiveBenchMathBench` baseline.

## Regression Prevention
- Run full eval on val after each prompt change.
- Compare aggregate scores per-task-family if available; a regression on one family but not others signals prompt over-fit.

## Chain-Level Optimization Scope

- **Structural changes**: NOT in-scope. Chain is fixed at 1 node.
- **Parameter changes**: NOT in-scope. Model settings are fixed to match GEPA's fairness envelope.
- **Prompt changes**: In-scope. Only modify `prompts/modules/solve/variant-*.md`.

## Lessons Logging
- Record iteration outcomes in `docs/change-log.md`.
