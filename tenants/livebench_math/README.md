<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# livebench_math

## Purpose
LiveBench-Math tenant mirroring the GEPA paper's (arXiv:2507.19457) `LiveBenchMathBench`.
Used for head-to-head comparison of FEPO against GEPA across 5 math task families
(AMC/SMC, AIME, IMO/USAMO, AMPS_Hard).

## Status
- Lifecycle: active
- Last validated: 2026-05-08
- Primary artifact set: 121 train / 121 val / 126 test (from HuggingFace `livebench/math` test split)

## Quick Links
- Tenant profile: `docs/tenant-profile.md`
- Data contract: `docs/data-contract.md`
- Prompt contract: `docs/prompt-contract.md`
- Eval operations: `docs/eval-operations.md`
- Iteration playbook: `docs/iteration-playbook.md`
- Change log: `docs/change-log.md`

## Quick Run
- Build dataset (downloads from HuggingFace, replicates GEPA's `LiveBenchMathBench` splits exactly):
  - `python tenants/livebench_math/code/build_cases_jsonl.py`
  - Produces `train.jsonl` (121), `val.jsonl` (121), `test.jsonl` (126) in `datasets/datasets/`
- Run eval locally:
  - `export GEPA_ARTIFACT_PATH=/Users/basaglam/Desktop/FEPO/gepa-artifact`
  - `python -m hephaestus.cli eval --config tenants/livebench_math/configs/local-chain-variant001.json`

## Scorer Dependency
The scorer imports `livebenchmath_utils.metric.calculate_livebench_score` from
the GEPA artifact at runtime. Set `GEPA_ARTIFACT_PATH` before running the
scorer; otherwise eval raises a clear `ImportError` pointing at `docs/eval-operations.md`.

## Data Safety
- Do not modify `source_artifacts/` unless explicitly requested.
- Keep secrets out of committed files.
