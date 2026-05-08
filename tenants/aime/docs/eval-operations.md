<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Dataset
Data is sourced from HuggingFace `AI-MO/aimo-validation-aime` (train/val) and
`MathArena/aime_2025` (test × 5), split using the exact algorithm from
`gepa_artifact.benchmarks.AIME.AIMEBench`. Sizes: 45 train / 45 val / 150 test.

Build with: `python tenants/aime/code/build_cases_jsonl.py`

The JSONL files are committed to git; the builder produces byte-identical output
and a `splits.meta.json` fingerprint guards against drift.

## Config Matrix
- `local-chain-variant001.json` — baseline 1-node solve chain, local run on val.
- `remote-chain-variant001.json` — same chain, K8s-friendly (max_workers=16).

## Standard Eval Commands

Local:
- `python -m hephaestus.cli eval --config tenants/aime/configs/local-chain-variant001.json`

K8s (if cluster configured):
- `deploy/scripts/run_eval.sh --config tenants/aime/configs/remote-chain-variant001.json --detach`

## Success Criteria
- Baseline target: match GEPA paper's reported `AIMEBench` score within run-to-run variance (temperature=1.0 adds ~3pp).

## Failure Triage
- Check `summary.md` for aggregate EM and parse rate.
- If `parse_ok` rate is low, the prompt likely does not constrain output to an integer; iterate on the prompt.
- If `exact_match` is low but `parse_ok` is high, the model is parsing correctly but answering wrong; iterate on reasoning quality.

## Output Management
- `evals/tmp/` is local-only for scratch runs and is not committed.
- Archive notable runs to `evals/archive/` with descriptive names.
