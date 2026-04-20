<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Global references:
  - `docs/processes/prompt-iteration-loop.md`
- BM25 index built (auto-downloads on first eval run).
- Baseline chain eval completed with results in `evals/tmp/`.

## Iteration Loop
1. Follow the global iteration loop from `docs/processes/prompt-iteration-loop.md`.
2. Optimize prompts over the training split (`train.jsonl`, 150 cases). Follow Data Hygiene rules below for what analysis is allowed per split.
3. Evaluate on the validation split (`val.jsonl`, 300 cases) after each change. Only check aggregate scores (EM, F1) — do not inspect individual val cases.
4. Iterate until tenant success criteria are met.

## Data Hygiene

These rules prevent overfitting by separating prompt-design data from evaluation data. The optimization agent **must** follow them.

| Split | File | Access Level |
|-------|------|-------------|
| **Train** | `train.jsonl` (150 cases) | **Full access.** Inspect individual questions, answers, model outputs, and failure patterns. Use for all prompt design and failure analysis. |
| **Val** | `val.jsonl` (300 cases) | **Aggregate scores only.** Check EM and F1 totals to validate generalization. **Never** inspect individual questions, answers, or per-case results. |
| **Test** | `test.jsonl` | **Aggregate scores only.** Run once at the end for final confirmation. **Never** inspect individual cases. |

**Rules:**
1. All failure analysis, pattern extraction, and prompt-design reasoning must use **train** results exclusively.
2. Val and test results must only be used to read aggregate EM/F1 scores — never to inform prompt wording or design decisions.
3. If a val score regresses, re-analyze **train** failures to understand why — do not look at val cases to diagnose the issue.

## Prompt Module Optimization Status

The chain has 4 LLM prompt modules (2 retrieval nodes use BM25, not prompts):

| Module | Role |
|--------|------|
| `generate_answer` | Final answer from all context |
| `summarize2` | Summarize hop-2 retrieval |
| `summarize1` | Summarize hop-1 retrieval |
| `generate_query_with_context` | Generate follow-up query for hop 2 |

### Scope Constraint

The optimization agent must **only** modify prompt template files (`prompts/modules/*/variant-*.md`).
It must **not** change any of the following — these require explicit user approval:

- Retrieval parameters (`retrieval_k`, `bm25_data_dir`)
- Model settings (`temperature`, `top_p`, `model`, `max_tokens`)
- Chain architecture (`chains/multi_hop.py`, node wiring, retry/verification steps)
- Scorer logic or evaluation config

For reference, non-prompt approaches that *could* improve scores (but are out of scope for automated optimization):
- Temperature reduction (could reduce variance by 2-3pp)
- Retrieval improvements (BM25 k increase, passage re-ranking, query expansion)
- Chain architecture changes (retry/verification steps, self-consistency decoding)
- Dataset augmentation (synthetic examples for persistent failure patterns)

### Temperature variance reminder:
With temp=1.0, single-run metrics fluctuate ~3pp. The val split (300 cases) is more reliable than train (150 cases). Only accept changes showing 3+pp consistent improvement on BOTH splits.

## Stop Criteria
- EM >= 38% on the 300-case fullwiki validation split after optimizing over training data (matching GEPA baseline).

## Regression Prevention
- Run full chain eval on the validation split after each prompt change.
- Compare EM and F1 against previous best before accepting a new variant.

## Chain-Level Optimization Scope

The optimization agent reads this section to determine allowed optimization levels.

- **Structural changes**: NOT in-scope. Chain architecture (`chains/multi_hop.py`, node wiring, retry/verification steps) is fixed. Do not create chain variants.
- **Parameter changes**: NOT in-scope. Retrieval parameters (`retrieval_k`, `bm25_data_dir`), model settings (`temperature`, `top_p`, `model`, `max_tokens`) are fixed.
- **Prompt changes**: In-scope. Only modify prompt template files (`prompts/modules/*/variant-*.md`).

## Lessons Logging
- Record iteration outcomes in `docs/change-log.md`.
