<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# LiveBench Math Tenant

Multi-domain mathematical reasoning benchmark from LiveBench. Covers AMC/SMC
(multiple choice), AIME (integer), IMO/USAMO (proof rearrangement), and AMPS
Hard (symbolic equivalence).

## Quick Start

```bash
# Build datasets from HuggingFace
python tenants/livebench_math/code/build_cases_jsonl.py

# Run evaluation
python -m hephaestus.cli eval --config tenants/livebench_math/configs/local-chain-variant001.json

# Run tests
python -m pytest tenants/livebench_math/tests/ -v
```

## Structure

- `chains/solve.py` — 1-node CoT chain (same pattern as aime2025)
- `code/scorers/livebench_math_scorer.py` — Task-dispatch scorer
- `code/scoring_utils/` — Bundled scoring implementations per task type
- `prompts/variants/` — Prompt variants for optimization
- `docs/` — Tenant documentation

## Dependencies

```bash
pip install -e ".[livebench_math]"
```

Requires: `sympy`, `lark`, `Levenshtein`
