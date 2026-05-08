<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Global references:
  - `docs/processes/prompt-iteration-loop.md`
- Dataset present at `datasets/datasets/{train,val,test}.jsonl`.
- BM25 index at `tenants/hotpotqa/data/bm25/` (auto-builds on first hotpotqa run).
- Baseline chain eval completed with results in `evals/tmp/`.

## Iteration Loop
1. Follow the global iteration loop from `docs/processes/prompt-iteration-loop.md`.
2. Optimize prompts over train (`train.jsonl`, 150 cases).
3. Evaluate on val (`val.jsonl`, 300 cases) after each change. Only check aggregate scores (`retrieval_subset`, `title_recall`) — do not inspect individual val cases.
4. Iterate until tenant success criteria are met.

## Data Hygiene

| Split | File | Access Level |
|-------|------|-------------|
| **Train** | `train.jsonl` (150 cases) | **Full access.** Inspect claims, gold titles, retrieved passages, failure patterns. |
| **Val** | `val.jsonl` (300 cases) | **Aggregate scores only.** |
| **Test** | `test.jsonl` (300 cases) | **Aggregate scores only. Run once at the end.** |

## Prompt Module Optimization Status

The chain has 4 LLM prompt modules (3 retrieval nodes use BM25, not prompts):

| Module | Role |
|--------|------|
| `summarize1` | Summarize hop-1 retrieved passages |
| `summarize2` | Summarize hop-2 retrieved passages (has access to summarize1 output) |
| `create_query_hop2` | Generate follow-up search query for hop 2 |
| `create_query_hop3` | Generate follow-up search query for hop 3 |

## Stop Criteria
- Reach target `retrieval_subset` on val that matches or beats GEPA paper's reported `hoverBench` baseline.

## Regression Prevention
- Run full chain eval on val after each prompt change.
- Compare aggregate subset rate and recall against previous best before accepting a new variant.

## Chain-Level Optimization Scope

- **Structural changes**: NOT in-scope. Chain is fixed at 7 nodes matching GEPA's `HoverMultiHop`.
- **Parameter changes**: NOT in-scope. Retrieval k-values (7, 7, 10) and model settings are fixed to match GEPA's fairness envelope.
- **Prompt changes**: In-scope. Only modify `prompts/modules/*/variant-*.md`.

## Lessons Logging
- Record iteration outcomes in `docs/change-log.md`.
