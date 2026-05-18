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

## Fixed Experimental Parameters

Immutable for the duration of this study (GEPA comparison fairness):
- `temperature`: 1.0
- `top_p`: 0.95
- `model`: gpt-4.1-mini
- `max_tokens`: 16000

These must not be modified by any agent or optimization process. See `docs/processes/prompt-iteration-loop.md` § Experimental Constants.

## Budget
- **30 variant budget** — maximum 30 prompt variants total.
- **Prompt-only optimization** — do not modify chain structure, scorer, or parameters. Only iterate on prompt text in `prompts/variants/`.

## Stop Criteria
- Accuracy >= 60% on val split.
- Or: variant budget exhausted (30 variants).
- Or: 3 consecutive iterations with no improvement.

## Regression Prevention
- Always evaluate on test split after optimization (never optimize on test).
- Track all variant scores in change-log.

## Lessons Logging
- Record insights in `docs/change-log.md` with date, variant, model, and accuracy delta.
