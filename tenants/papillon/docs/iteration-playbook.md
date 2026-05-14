<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Datasets built via `code/build_cases_jsonl.py`.
- OPENAI_API_KEY set (needed for untrusted model and judge calls).

## Iteration Loop
1. Run baseline eval on val split.
2. Analyze train-split failures: leakage vs quality issues.
3. For leakage: improve redaction prompt to catch more PII patterns.
4. For quality: improve reconstruction prompt to better leverage untrusted response.

## Stop Criteria
- Composite score >= 94% on val split.
- Or: 3 consecutive iterations with no improvement.

## Scope Constraint
- Only modify prompt templates.
- Do NOT change untrusted model, judge model, or scoring logic.
