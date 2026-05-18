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

Local:
- `python -m hephaestus.cli eval --config tenants/papillon/configs/local-chain-variant001.json`

Remote (K8s):
- `deploy/scripts/run_eval.sh --config tenants/papillon/configs/remote-chain-variant001.json --detach`

## Success Criteria
Target threshold: **94%** composite score on the validation split.

## Failure Triage
- If privacy score is low: check redaction output for leaked PII in step_outputs.
- If quality score is low: check reconstruction prompt quality and untrusted model response.

## Output Management
- `evals/tmp/` is local-only for scratch runs and is not committed.
- Archive notable runs to `evals/archive/` with descriptive names.

## Cost Note
Each case requires 2 trusted LLM calls + 1 untrusted LLM call + 2 judge calls = 5 API calls.
Budget accordingly.
