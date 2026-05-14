<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# aime2025 tenant

AIME 2025 math competition benchmark for evaluating prompt optimization methods.
Replicates the setup from ETGPO (arxiv 2602.00997) for direct comparison with
GEPA, MIPROv2, and ETGPO.

## Dataset

- **Validation**: 90 problems from AIME 2022-2024 (for prompt optimization)
- **Test**: 30 problems from AIME 2025 (for final evaluation)

## Comparison targets (from ETGPO paper)

| Method | GPT-4.1-mini | DeepSeek-V3.1 |
|--------|-------------|---------------|
| CoT baseline | 47.08 | 65.52 |
| GEPA | 49.06 | 64.48 |
| MIPROv2 | 47.66 | 68.23 |
| ETGPO | 49.06 | 69.74 |

## Running

```bash
# Build datasets
python tenants/aime2025/code/build_cases_jsonl.py

# Run eval (K8s)
NAMESPACE=your-namespace bash deploy/scripts/run_eval.sh \
  --config tenants/aime2025/configs/local-gpt41mini-test-variant001.json --detach
```
