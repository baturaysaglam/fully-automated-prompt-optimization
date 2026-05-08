<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Dataset
Data is sourced from local IFBench JSONL files shipped inside the gepa-artifact
repo (`gepa_artifact/benchmarks/IFBench/data/`). Split using the exact algorithm
from `gepa_artifact.benchmarks.IFBench.IFBench`:
- val = `train.jsonl[:300]`
- train = `train.jsonl[300:600]`
- test = `test.jsonl` (all 294 rows)
Then `trim_dataset(seed=1)` with caps 150/300/300.

Post-trim sizes: 150 train / 300 val / 294 test.

Build with:
```
export GEPA_ARTIFACT_PATH=/Users/basaglam/Desktop/FEPO/gepa-artifact
python tenants/ifbench/code/build_cases_jsonl.py
```

## Scorer Dependency

The scorer imports `instructions_registry.INSTRUCTION_DICT` from the gepa-artifact
repo at runtime. That registry depends on several Python packages that are NOT
default FEPO deps:

- `nltk` (with `punkt_tab` downloaded)
- `spacy` (with an English model, e.g. `en_core_web_sm`)
- `syllapy`
- `emoji`
- `immutabledict`

Install them into the FEPO env before running the eval:

```
pip install nltk spacy syllapy emoji immutabledict
python -c "import nltk; nltk.download('punkt_tab')"
python -m spacy download en_core_web_sm
```

If any of these are missing, the scorer raises a clear `ImportError` at score
time naming the missing deps. Unit tests skip automatically under
`@pytest.mark.requires_ifbench_deps`.

## Config Matrix
- `local-chain-variant001.json` — baseline 2-node chain, local run on val.
- `remote-chain-variant001.json` — same chain, K8s-friendly (max_workers=16).

## Standard Eval Commands

```
export GEPA_ARTIFACT_PATH=/Users/basaglam/Desktop/FEPO/gepa-artifact
python -m hephaestus.cli eval --config tenants/ifbench/configs/local-chain-variant001.json
```

## Success Criteria
- Baseline target: match GEPA paper's reported `IFBench` score on val within run-to-run variance.

## Failure Triage
- Low `instruction_pass_rate` concentrated in one instruction family → iterate on the `ensure_correct_response` prompt to better handle that family.
- `scorer_ok = 0` rate high → likely an env issue (missing `nltk` data, spacy model, etc.). Check logs for the import error.
- Drafts without asterisks but passing post-revision → confirms the two-stage design is useful; keep.

## Output Management
- `evals/tmp/` is local-only for scratch runs and is not committed.
- Archive notable runs to `evals/archive/` with descriptive names.
