<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## v0.1.0 — 2026-03-31

- Initial tenant setup
- Dataset builder pulling from HuggingFace (val: 2022-2024, test: 2025)
- AIME scorer with exact match + LLM equivalence checking
- Single-node CoT chain
- variant-001: baseline CoT prompt from ETGPO paper
- Configs for GPT-4.1-mini and DeepSeek-V3.1

## Baseline — 2026-03-31

GPT-4.1-mini, variant-001, temperature=1.0, 8 runs on test split (30 problems):

| Metric | Value |
|--------|-------|
| Mean accuracy | 46.67 +/- 1.99 |
| Individual runs | 40.0, 50.0, 56.7, 40.0, 50.0, 46.7, 43.3, 46.7 |

ETGPO paper comparison (GPT-4.1-mini, 64 runs):
- CoT baseline: 47.08 +/- 1.43
- GEPA: 49.06 +/- 1.51
- ETGPO: 49.06 +/- 1.36


