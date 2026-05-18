<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# IFBench Tenant

Instruction-following benchmark with diverse constraint types. Uses a 2-stage
generate-then-verify chain.

## Quick Start

```bash
# Build datasets from source artifacts
python tenants/ifbench/code/build_cases_jsonl.py

# Run evaluation
python -m hephaestus.cli eval --config tenants/ifbench/configs/local-chain-variant001.json

# Run tests
python -m pytest tenants/ifbench/tests/ -v
```

## Structure

- `chains/generate_verify.py` — 2-node chain: generate → verify
- `code/scorers/ifbench_scorer.py` — Instruction adherence fraction scorer
- `code/scoring_utils/` — Bundled instruction checking code (Allen AI, Apache-2.0)
- `source_artifacts/` — Raw JSONL data files from GEPA
- `prompts/modules/` — Prompt variants per chain node

## Dependencies

```bash
pip install -e ".[ifbench]"
```

Requires: `nltk`, `spacy`, `emoji`, `syllapy`
