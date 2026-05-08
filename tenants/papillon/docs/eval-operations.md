<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Dataset
Data is sourced from HuggingFace `Columbia-NLP/PUPA` config `pupa_new`, with
hardcoded sequential slicing matching `gepa_artifact.benchmarks.papillon.Papillon`:
111 train / 111 val / 221 test.

Build with: `python tenants/papillon/code/build_cases_jsonl.py`

**Fidelity note:** the GEPA artifact instantiates a dedicated
`dspy.LM("openai/gpt-4.1-mini")` for the untrusted LLM node. FEPO reuses the
shared provider (same model, same cost semantics). This keeps the 3-LLM-call
budget identical but simplifies plumbing.

## Config Matrix
- `local-chain-variant001.json` — baseline 3-node chain with LLM judge configured.
- `remote-chain-variant001.json` — same chain, K8s-friendly (max_workers=16).

## Standard Eval Commands

Requires `OPENAI_API_KEY` (the quality judge is an LLM call):

```
export OPENAI_API_KEY=...
python -m hephaestus.cli eval --config tenants/papillon/configs/local-chain-variant001.json
```

Without `OPENAI_API_KEY` the eval will fail on the first judge call. For
leakage-only testing without credentials, configure a `tenant_config` that
omits `judge_provider` — composite will treat quality as 0 but leakage will
still be measured.

## Success Criteria
- Baseline target: match GEPA paper's reported `Papillon` score on val within run-to-run variance.

## Failure Triage
- High `leakage_rate` → `craft_redacted_request` is not stripping PII. Iterate on that prompt.
- Low `quality` with zero leakage → `respond_to_query` is not composing an acceptable answer. Iterate on that prompt.
- Composite oddly low despite low leakage and high quality → sanity-check `compute_metrics` formula; both halves should contribute equally.

## Output Management
- `evals/tmp/` is local-only for scratch runs and is not committed.
- Archive notable runs to `evals/archive/` with descriptive names.
