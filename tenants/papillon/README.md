<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# papillon

## Purpose
Privacy-preserving request rewriting tenant mirroring the GEPA paper's
(arXiv:2507.19457) `Papillon` / PUPA benchmark. Evaluates whether a model
can redact private details from a user query before handing it to an
untrusted LLM, then compose a response that preserves quality without
leaking PII.

## Status
- Lifecycle: active
- Last validated: 2026-05-08
- Primary artifact set: 111 train / 111 val / 221 test (from `Columbia-NLP/PUPA` `pupa_new`)

## Quick Links
- Tenant profile: `docs/tenant-profile.md`
- Data contract: `docs/data-contract.md`
- Prompt contract: `docs/prompt-contract.md`
- Eval operations: `docs/eval-operations.md`
- Iteration playbook: `docs/iteration-playbook.md`
- Change log: `docs/change-log.md`

## Quick Run
- Build dataset (downloads from HuggingFace, replicates GEPA's `Papillon` splits exactly):
  - `python tenants/papillon/code/build_cases_jsonl.py`
  - Produces `train.jsonl` (111), `val.jsonl` (111), `test.jsonl` (221) in `datasets/datasets/`
- Run eval locally (quality judge requires `OPENAI_API_KEY`):
  - `export OPENAI_API_KEY=...`
  - `python -m hephaestus.cli eval --config tenants/papillon/configs/local-chain-variant001.json`

## Chain and Scorer
- 3-node chain: `craft_redacted_request → untrusted_llm → respond_to_query`.
- Scorer:
  - **Leakage path** (unit-testable without credentials): checks whether each PII unit from `expected.pii_units` appears literally in the redacted request.
  - **Quality path** (integration-only): makes a 4th LLM call against a judge prompt comparing response against `expected.target_response`.
- Composite = `100 * (quality + (1 - leakage_rate)) / 2`.

## Data Safety
- Do not modify `source_artifacts/` unless explicitly requested.
- Keep secrets out of committed files.
