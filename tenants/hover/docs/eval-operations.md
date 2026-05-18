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
- `python -m hephaestus.cli eval --config tenants/hover/configs/local-chain-variant001.json`

Remote (K8s):
- `deploy/scripts/run_eval.sh --config tenants/hover/configs/remote-chain-variant001.json --detach`

## Success Criteria
Target threshold: **60%** partial retrieval recall on the validation split.

## Prerequisites
- BM25 index built (auto-downloads wiki.abstracts.2017 on first run).
- Requires `bm25s`, `PyStemmer`, `ujson`, `diskcache` packages.

## Failure Triage
- If recall is low, check query generation quality in step_outputs.
- Verify BM25 index is built correctly in `data/bm25/`.

## Output Management
- `evals/tmp/` is local-only for scratch runs and is not committed.
- Archive notable runs to `evals/archive/` with descriptive names.
