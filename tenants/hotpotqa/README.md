<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# hotpotqa

## Purpose
Tenant for HotpotQA multi-hop question answering evaluation, replicating the GEPA paper's
(arXiv:2507.19457) pipeline with a 6-node LangGraph chain using in-process BM25 retrieval.

## Status
- Lifecycle: active
- Last validated: 2026-03-03
- Primary artifact set: HotpotQA fullwiki (150 train / 300 val / 300 test)

## Quick Links
- Tenant profile: `docs/tenant-profile.md`
- Data contract: `docs/data-contract.md`
- Prompt contract: `docs/prompt-contract.md`
- Eval operations: `docs/eval-operations.md`
- Iteration playbook: `docs/iteration-playbook.md`
- Change log: `docs/change-log.md`

## Quick Run
- Build dataset (downloads from HuggingFace, replicates DSPy/GEPA splits):
  - `python tenants/hotpotqa/code/build_cases_jsonl.py`
  - Produces `train.jsonl` (150), `val.jsonl` (300), `test.jsonl` (300) in `datasets/datasets/`
- Run eval on k8s (default, requires `$NAMESPACE`):
  - `deploy/scripts/run_eval.sh --config tenants/hotpotqa/configs/remote-chain-variant001.json --detach`
- Run eval locally (fallback):
  - `python -m hephaestus.cli eval --config tenants/hotpotqa/configs/local-chain-variant001.json`

## Data Safety
- Do not modify `source_artifacts/` unless explicitly requested.
- Keep secrets out of committed files.
