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
- Direct: `python -m hephaestus.cli eval --config tenants/ifbench/configs/<config>.json`

## Success Criteria
Target threshold: **60%** on the test split.

## Failure Triage
- Check per-instruction breakdown in feedback for systematic failures.
- Val/test use different instruction categories — val regression does not predict test regression.
- NLTK punkt tokenizer must be downloaded (auto-downloads on first use).

## Output Management
- `evals/tmp/` — transient eval outputs, not committed.
- Results summarized in `docs/change-log.md`.
