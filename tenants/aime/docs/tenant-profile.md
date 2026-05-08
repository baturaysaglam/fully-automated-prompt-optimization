<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
- Math competition question answering mirroring the GEPA paper's (arXiv:2507.19457) `AIMEBench`.
- Used for head-to-head comparison of FEPO against GEPA baseline on AIME problems.

## Security Environment Assumptions
- Inputs are publicly available math competition problems (AIME 2022-2024 and AIME 2025).
- No retrieval; a single LLM call produces a reasoning + integer answer.

## Threat Model Focus
- Evaluation accuracy: exact integer match against gold answers.
- Parse robustness: model outputs must be reduced to a single integer by the scorer.

## Known Safe Patterns
- All gold answers are integers in the range 0-999 (AIME convention).
- Problems are public, derived from HuggingFace datasets with no PII.

## Tenant Terminology
- "AIME": American Invitational Mathematics Examination — an annual US math competition whose problems this benchmark uses.
- "GEPA": the paper (arXiv:2507.19457) whose `AIMEBench` splits this tenant mirrors.
- "ETGPO": a separate baseline (arxiv 2602.00997) tracked in the sibling `tenants/aime2025/` tenant. This tenant does **not** share splits with `aime2025`.
