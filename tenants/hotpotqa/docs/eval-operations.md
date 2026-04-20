<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Dataset
Data is sourced from HuggingFace `hotpot_qa` `fullwiki` and split using the
DSPy/GEPA pipeline (all examples, sequential 40/40/20 test/val/train split,
seed=1 sampling).  Default split sizes: 150 train / 300 val / 300 test.

Build with: `python tenants/hotpotqa/code/build_cases_jsonl.py`

## Config Matrix
- `local-chain-variant001.json` — full 9-node chain eval on 300 val cases.

## Standard Eval Commands

Default: run on k8s (requires `$NAMESPACE` to be set):
- `deploy/scripts/run_eval.sh --config tenants/hotpotqa/configs/remote-chain-variant001.json --detach`

Local fallback:
- `python -m hephaestus.cli eval --config tenants/hotpotqa/configs/local-chain-variant001.json`

## K8s Eval (K8s cluster)

See [deploy/README.md](../../../deploy/README.md) for cluster setup and full docs.

```bash
deploy/scripts/run_eval.sh --config tenants/hotpotqa/configs/remote-chain-variant001.json --detach
```

Each run creates a dedicated pod named `hephaestus-hotpotqa-<hash>` with isolated workspace and results.

## Success Criteria
- Baseline target: ~38% EM (+/-5%) on 300-case fullwiki val split (matching GEPA Table 2).

## Failure Triage
- Check `summary.md` for aggregate EM and F1 scores.
- Inspect `results.jsonl` step_outputs for retrieval quality and intermediate reasoning.
- Verify BM25 index is built and returning relevant passages (auto-builds on first run).

## Output Management
- `evals/tmp/` is local-only for scratch runs and is not committed.
- Archive notable runs to `evals/archive/` with descriptive names.
