<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# aime

## Purpose
AIME math competition tenant mirroring the GEPA paper's (arXiv:2507.19457) `AIMEBench`
splits byte-for-byte. Used for head-to-head comparison of FEPO against GEPA.

## Status
- Lifecycle: active
- Last validated: 2026-05-08
- Primary artifact set: 45 train / 45 val (AI-MO/aimo-validation-aime) / 150 test (MathArena/aime_2025 × 5)

## Quick Links
- Tenant profile: `docs/tenant-profile.md`
- Data contract: `docs/data-contract.md`
- Prompt contract: `docs/prompt-contract.md`
- Eval operations: `docs/eval-operations.md`
- Iteration playbook: `docs/iteration-playbook.md`
- Change log: `docs/change-log.md`

## Quick Run
- Build dataset (downloads from HuggingFace, replicates GEPA's `AIMEBench` splits exactly):
  - `python tenants/aime/code/build_cases_jsonl.py`
  - Produces `train.jsonl` (45), `val.jsonl` (45), `test.jsonl` (150) in `datasets/datasets/`
- Run eval locally:
  - `python -m hephaestus.cli eval --config tenants/aime/configs/local-chain-variant001.json`

## Relationship to `tenants/aime2025/`
This tenant mirrors the GEPA artifact's `AIMEBench`. The separate `tenants/aime2025/`
tenant mirrors ETGPO's setup (AIME 2022-2024 for val, AIME 2025 for test) and is
maintained for a different comparison axis. The two tenants do not share data or prompts.

## Data Safety
- Do not modify `source_artifacts/` unless explicitly requested.
- Keep secrets out of committed files.
