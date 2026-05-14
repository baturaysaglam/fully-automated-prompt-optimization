<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Config Matrix
| Config | Prompt Variant | Dataset | Model |
|--------|---------------|---------|-------|
| (generated at runtime) | `variant-002.md` | `test.jsonl` | gpt-4.1-mini |

## Standard Eval Commands
- Preferred: `/project:eval-runner` with a smoke_test config.
- Direct: `python -m hephaestus.cli eval --config tenants/smoke_test/configs/<config>.json`
- Integration test: `OPENAI_API_KEY=... pytest -m integration -v`

## Success Criteria
- 100% exact_match on all cases with `variant-002`.
- 0% exact_match with `variant-001` (confirms the bad variant is indeed bad).

## Failure Triage
- If `variant-002` does not achieve 100%: check that the model is respecting the single-word output constraint. Look for trailing punctuation or extra whitespace.
- If `variant-001` starts passing: the scorer or dataset may have changed — investigate.

## Output Management
- Eval outputs are transient and local-only; not committed.
- Results are summarized in `docs/change-log.md`.
