<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Datasets built via `code/build_cases_jsonl.py` and pushed to GCS.
- Baseline eval completed on val split.
- OPENAI_API_KEY set in environment.

## Iteration Loop
1. Run baseline eval on val split to establish starting accuracy.
2. Use the `optimization` agent on the val config to optimize the prompt.
3. Evaluate optimized variant on test split.
4. Compare against ETGPO paper baselines (GEPA, MIPROv2, ETGPO).

## Budget
- **30 variant budget** — maximum 30 prompt variants total.
- **Prompt-only optimization** — do not modify chain structure, scorer, or parameters. Only iterate on prompt text in `prompts/variants/`.

## Stop Criteria
- Accuracy on test split meets or exceeds GEPA scores (49.06 for GPT-4.1-mini).
- Or: variant budget exhausted (30 variants).
- Or: 3 consecutive iterations with no improvement.

## Regression Prevention
- Always evaluate on test split after optimization (never optimize on test).
- Track all variant scores in change-log.

## Lessons Logging
- Record insights in `docs/change-log.md` with date, variant, model, and accuracy delta.
