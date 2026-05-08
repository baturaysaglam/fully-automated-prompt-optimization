<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Dataset
Data is sourced from HuggingFace `hover` (train split, filtered to 3-unique-doc
examples), split using the exact algorithm from
`gepa_artifact.benchmarks.hover.hoverBench`. Sizes: 150 train / 300 val / 300 test.

Build with: `python tenants/hover/code/build_cases_jsonl.py`

The JSONL files are committed to git; the builder produces byte-identical output
and a `splits.meta.json` fingerprint guards against drift.

## Config Matrix
- `local-chain-variant001.json` — baseline 7-node multi-hop retrieval chain, local run on val.
- `remote-chain-variant001.json` — same chain, K8s-friendly (max_workers=16).

## Standard Eval Commands

Prerequisite: the BM25 index at `tenants/hotpotqa/data/bm25/` must exist.
It auto-builds on the first hotpotqa eval run; the hover chain reuses it.

Local:
- `python -m hephaestus.cli eval --config tenants/hover/configs/local-chain-variant001.json`

K8s (if cluster configured):
- `deploy/scripts/run_eval.sh --config tenants/hover/configs/remote-chain-variant001.json --detach`

## Success Criteria
- Baseline target: match GEPA paper's reported `hoverBench` retrieval-subset score on val within run-to-run variance (temperature=1.0 adds ~3pp).

## Failure Triage
- Check `summary.md` for aggregate retrieval-subset rate and `title_recall`.
- Low `title_recall` → queries not targeting the right entities: iterate on `create_query_hop2/hop3` prompts.
- High `title_recall` but subset failing → missing 1-2 titles; inspect which hop failed to retrieve them and iterate on the corresponding summarize prompt.

## Output Management
- `evals/tmp/` is local-only for scratch runs and is not committed.
- Archive notable runs to `evals/archive/` with descriptive names.
