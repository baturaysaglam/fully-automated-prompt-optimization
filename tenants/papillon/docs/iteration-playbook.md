<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Global references:
  - `docs/processes/prompt-iteration-loop.md`
- Dataset present at `datasets/datasets/{train,val,test}.jsonl`.
- `OPENAI_API_KEY` exported (quality judge requires LLM calls).
- Baseline chain eval completed.

## Iteration Loop
1. Follow the global iteration loop from `docs/processes/prompt-iteration-loop.md`.
2. Optimize prompts over train (`train.jsonl`, 111 cases).
3. Evaluate on val (`val.jsonl`, 111 cases). Only check aggregate `composite`, `quality`, `leakage_rate`.
4. Iterate until success criteria are met.

## Data Hygiene

| Split | File | Access Level |
|-------|------|-------------|
| **Train** | `train.jsonl` (111 cases) | **Full access.** Inspect user queries, gold responses, PII units. |
| **Val** | `val.jsonl` (111 cases) | **Aggregate scores only.** |
| **Test** | `test.jsonl` (221 cases) | **Aggregate scores only. Run once at the end.** |

## Prompt Module Optimization Status

The chain has 3 user-facing LLM modules plus a judge prompt:

| Module | Role | Scope |
|--------|------|-------|
| `craft_redacted_request` | Redact PII from user query | In-scope |
| `untrusted_llm` | Untrusted external LLM response | In-scope (it is still a prompt we control) |
| `respond_to_query` | Compose final user-facing response | In-scope |
| `judge` | Quality-comparison LLM judge | Out-of-scope for prompt optimization (changes would compromise fairness against GEPA) |

## Stop Criteria
- Reach target `composite` on val matching/beating GEPA's reported `Papillon` baseline.

## Regression Prevention
- Run full eval on val after each prompt change.
- Track both `quality` and `leakage_rate` separately — an improvement that lifts composite by worsening one half is a red flag.

## Chain-Level Optimization Scope

- **Structural changes**: NOT in-scope. The 3-node chain matches GEPA's `PAPILLON` program.
- **Parameter changes**: NOT in-scope. Model settings are fixed to match GEPA's fairness envelope.
- **Prompt changes**: In-scope for `craft_redacted_request`, `untrusted_llm`, `respond_to_query`. The `judge` prompt is locked.

## Lessons Logging
- Record iteration outcomes in `docs/change-log.md`.
