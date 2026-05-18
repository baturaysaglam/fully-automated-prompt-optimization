<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Global references:
  - `docs/processes/prompt-iteration-loop.md`
- Tenant-specific: faith must be installed (`pip install -e ".[cti_rcm]"`), dataset must be built via `build_cases_jsonl.py`.

## Iteration Loop
1. Follow the global iteration loop from `docs/processes/prompt-iteration-loop.md`. For automated optimization, use the `optimization` agent.
2. Key failure patterns to watch: `answer_format: "invalid"` (model not outputting parseable CWE ID), wrong CWE family (e.g., CWE-79 vs CWE-80).
3. Re-run evals and iterate until tenant success criteria are met.

## Fixed Experimental Parameters

Immutable for the duration of this study (GEPA comparison fairness):
- `temperature`: 1.0
- `top_p`: 0.95
- `model`: as set in the baseline config (must not change within an optimization run)
- `max_tokens`: 16000

These must not be modified by any agent or optimization process. See `docs/processes/prompt-iteration-loop.md` § Experimental Constants.

## Optimization Scope
- **Prompt-only optimization** — no chain or parameter changes.
- **Budget**: 25 prompt variants maximum.

## Stop Criteria
- Accuracy plateaus across 3+ consecutive variants with different strategies.
- All `answer_format: "invalid"` cases reduced below 5%.
- Variant budget (25) exhausted.

## Regression Prevention
- Compare new variant against baseline on full 1000-case test set.
- Check that `answer_format` distribution does not regress (fewer "proper" extractions).

## Lessons Logging
- Record insights in `docs/change-log.md` with date, variant, and accuracy delta.
