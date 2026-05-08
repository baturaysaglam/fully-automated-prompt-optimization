<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Global references:
  - `docs/processes/prompt-iteration-loop.md`
- Dataset present at `datasets/datasets/{train,val,test}.jsonl`.
- `GEPA_ARTIFACT_PATH` exported.
- Scorer deps (nltk, spacy, syllapy, emoji, immutabledict) installed in env.
- Baseline chain eval completed.

## Iteration Loop
1. Follow the global iteration loop from `docs/processes/prompt-iteration-loop.md`.
2. Optimize prompts over train (`train.jsonl`, 150 cases).
3. Evaluate on val (`val.jsonl`, 300 cases). Aggregate `instruction_pass_rate` only.
4. Iterate until success criteria are met.

## Data Hygiene

| Split | File | Access Level |
|-------|------|-------------|
| **Train** | `train.jsonl` (150 cases) | **Full access.** Inspect prompts, instruction ids, model outputs, per-instruction pass/fail. |
| **Val** | `val.jsonl` (300 cases) | **Aggregate scores only.** |
| **Test** | `test.jsonl` (294 cases) | **Aggregate scores only. Run once at the end.** |

## Prompt Module Optimization Status

The chain has 2 LLM prompt modules:

| Module | Role |
|--------|------|
| `generate_response` | Produce a first-pass response to the user prompt |
| `ensure_correct_response` | Revise the draft to satisfy constraints |

## Stop Criteria
- Reach target `instruction_pass_rate` on val matching/beating GEPA's reported `IFBench` baseline.

## Regression Prevention
- Run full eval on val after each prompt change.
- Check the breakdown of pass/fail per instruction family on train when possible — avoid optimizing for one family at the cost of others.

## Chain-Level Optimization Scope

- **Structural changes**: NOT in-scope. 2-node chain matches GEPA's program.
- **Parameter changes**: NOT in-scope.
- **Prompt changes**: In-scope for `generate_response` and `ensure_correct_response`.

## Lessons Logging
- Record iteration outcomes in `docs/change-log.md`.
