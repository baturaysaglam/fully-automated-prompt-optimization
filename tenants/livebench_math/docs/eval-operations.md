<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Config Matrix
| Config | Model | Split | Purpose |
|--------|-------|-------|---------|
| `local-chain-variant001.json` | GPT-4.1-mini | val | Optimization |
| `local-chain-variant001-test.json` | GPT-4.1-mini | test | Final eval |

## Standard Eval Commands
- Preferred: `/project:eval-runner` with the appropriate config.
- Direct: `python -m hephaestus.cli eval --config tenants/livebench_math/configs/<config>.json`

## Success Criteria
Target threshold: **64%** on the validation split (matching GEPA+Merge GPT-4.1-mini result).

## Failure Triage
- Check `evals/tmp/<run>/summary.md` for aggregate scores.
- Check `evals/tmp/<run>/results.jsonl` for per-case breakdown.
- If AMPS_Hard cases timeout, check SymPy parse errors in feedback.
- Temperature=1.0 means variance per run; use multiple runs for reliable scores.

## Output Management
- `evals/tmp/` — transient eval outputs, not committed.
- Eval outputs are local-only; results are summarized in `docs/change-log.md`.
