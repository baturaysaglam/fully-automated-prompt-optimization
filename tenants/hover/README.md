<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# hover

## Purpose
Three-hop claim-retrieval tenant mirroring the GEPA paper's (arXiv:2507.19457) `hoverBench`.
Used for head-to-head comparison of FEPO against GEPA on multi-hop retrieval tasks.

## Status
- Lifecycle: active
- Last validated: 2026-05-08
- Primary artifact set: 150 train / 300 val / 300 test (HoVer with 3-unique-doc filter)

## Quick Links
- Tenant profile: `docs/tenant-profile.md`
- Data contract: `docs/data-contract.md`
- Prompt contract: `docs/prompt-contract.md`
- Eval operations: `docs/eval-operations.md`
- Iteration playbook: `docs/iteration-playbook.md`
- Change log: `docs/change-log.md`

## Quick Run
- Build dataset (downloads from HuggingFace, replicates GEPA's `hoverBench` splits exactly):
  - `python tenants/hover/code/build_cases_jsonl.py`
  - Produces `train.jsonl` (150), `val.jsonl` (300), `test.jsonl` (300) in `datasets/datasets/`
- Run eval locally (requires BM25 corpus from `tenants/hotpotqa/data/bm25/`, auto-built on first hotpotqa run):
  - `python -m hephaestus.cli eval --config tenants/hover/configs/local-chain-variant001.json`

## Retrieval Backend
The 7-node chain reuses `tenants/hotpotqa/code/retrieval.py` (BM25 over `wiki.abstracts.2017`).
No separate corpus is built — `bm25_data_dir` points at hotpotqa's shared index.

## Data Safety
- Do not modify `source_artifacts/` unless explicitly requested.
- Keep secrets out of committed files.
