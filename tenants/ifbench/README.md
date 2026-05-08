<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# ifbench

## Purpose
Instruction-following benchmark tenant mirroring the GEPA paper's (arXiv:2507.19457)
`IFBench` — evaluates whether a model's response obeys explicit format / count /
structure constraints embedded in the prompt.

## Status
- Lifecycle: active
- Last validated: 2026-05-08
- Primary artifact set: 150 train / 300 val / 294 test (from IFBench local JSONL via gepa-artifact)

## Quick Links
- Tenant profile: `docs/tenant-profile.md`
- Data contract: `docs/data-contract.md`
- Prompt contract: `docs/prompt-contract.md`
- Eval operations: `docs/eval-operations.md`
- Iteration playbook: `docs/iteration-playbook.md`
- Change log: `docs/change-log.md`

## Quick Run
- Build dataset (reads IFBench JSONL files from the gepa-artifact repo):
  - `export GEPA_ARTIFACT_PATH=/Users/basaglam/Desktop/FEPO/gepa-artifact`
  - `python tenants/ifbench/code/build_cases_jsonl.py`
  - Produces `train.jsonl` (150), `val.jsonl` (300), `test.jsonl` (294) in `datasets/datasets/`
- Run eval locally:
  - `export GEPA_ARTIFACT_PATH=/Users/basaglam/Desktop/FEPO/gepa-artifact`
  - Ensure `nltk`, `spacy`, `syllapy`, `emoji`, `immutabledict` are installed in the env (see `docs/eval-operations.md`)
  - `python -m hephaestus.cli eval --config tenants/ifbench/configs/local-chain-variant001.json`

## Scorer Dependency
The scorer imports `instructions_registry.INSTRUCTION_DICT` from the GEPA
artifact at runtime (`GEPA_ARTIFACT_PATH`). The instruction library depends on
`nltk`, `spacy`, `syllapy`, `emoji`, and `immutabledict` — these must be
importable in the runtime env. Unit tests skip gracefully when these are missing.

## Data Safety
- Do not modify `source_artifacts/` unless explicitly requested.
- Keep secrets out of committed files.
