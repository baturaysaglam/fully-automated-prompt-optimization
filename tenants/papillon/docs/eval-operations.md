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

## Success Criteria
Target threshold: **94%** composite score on the validation split.

## Cost Note
Each case requires 2 trusted LLM calls + 1 untrusted LLM call + 2 judge calls = 5 API calls.
Budget accordingly.
