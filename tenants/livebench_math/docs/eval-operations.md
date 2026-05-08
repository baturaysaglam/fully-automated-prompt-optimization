<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Dataset
Data is sourced from HuggingFace `livebench/math` (test split), split using the
exact algorithm from `gepa_artifact.benchmarks.livebench_math.LiveBenchMathBench`.
Sizes: 121 train / 121 val / 126 test.

Build with: `python tenants/livebench_math/code/build_cases_jsonl.py`

## Config Matrix
- `local-chain-variant001.json` — baseline 1-node solve chain, local run on val.
- `remote-chain-variant001.json` — same chain, K8s-friendly (max_workers=16).

## Standard Eval Commands

Prerequisite: set `GEPA_ARTIFACT_PATH` so the scorer can import `livebenchmath_utils.metric`.

```
export GEPA_ARTIFACT_PATH=/Users/basaglam/Desktop/FEPO/gepa-artifact
python -m hephaestus.cli eval --config tenants/livebench_math/configs/local-chain-variant001.json
```

Without `GEPA_ARTIFACT_PATH`, the scorer raises an `ImportError` with remediation instructions.

## Success Criteria
- Baseline target: match GEPA paper's reported `LiveBenchMathBench` score on val within run-to-run variance (temperature=1.0 adds ~3pp).

## Failure Triage
- `livebench_score` low across all task families → prompt not producing reasoning/answer in an extractable form; iterate on the prompt.
- `scorer_ok = 0` → the scorer caught an exception inside `calculate_livebench_score`. Check logs; most likely causes are missing `question_d` metadata or a malformed model output that `calculate_livebench_score` cannot process.
- Zero scores concentrated in one task family → inspect a handful of `train` cases in that family and iterate on the prompt.

## Output Management
- `evals/tmp/` is local-only for scratch runs and is not committed.
- Archive notable runs to `evals/archive/` with descriptive names.
