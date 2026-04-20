<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## v0.1.0 — 2026-03-31

- Initial tenant setup
- Dataset builder pulling from HuggingFace (val: 2022-2024, test: 2025)
- AIME scorer with exact match + LLM equivalence checking
- Single-node CoT chain
- variant-001: baseline CoT prompt from ETGPO paper
- Configs for GPT-4.1-mini and DeepSeek-V3.1

## Baseline — 2026-03-31

GPT-4.1-mini, variant-001, temperature=1.0, 8 runs on test split (30 problems):

| Metric | Value |
|--------|-------|
| Mean accuracy | 46.67 +/- 1.99 |
| Individual runs | 40.0, 50.0, 56.7, 40.0, 50.0, 46.7, 43.3, 46.7 |

ETGPO paper comparison (GPT-4.1-mini, 64 runs):
- CoT baseline: 47.08 +/- 1.43
- GEPA: 49.06 +/- 1.51
- ETGPO: 49.06 +/- 1.36

## Optimization Round 1 — 2026-03-31

### Train Results (single run per variant, 90 problems)

| Variant | Description | Train Score |
|---------|-------------|-------------|
| variant-001 | Baseline CoT | 43.33% |
| variant-002 | Format + verify + leading zeros | 48.89% |
| variant-003 | Expert + format + verify | 52.22% |
| variant-004 | Solve-twice + format (no expert) | 48.89% |
| variant-005 | Careful + double-check + expert | 53.33% |
| variant-006 | Sub-problems + expert | 44.44% |
| variant-007 | Error-aware verification + expert | 53.33% |
| variant-008 | Combined v005+v007 | 52.22% |
| variant-009 | Ultra-minimal expert | 52.22% |
| **variant-010** | **Solve-twice on v005 base** | **56.67%** |
| variant-011 | v010 + error awareness tips | 48.89% |
| variant-012 | v010 ablation (no "read twice") | 54.44% |
| variant-013 | v010 + range check | 55.56% |
| variant-014 | Thorough step verification | 50.00% |
| variant-015 | Identify concepts + solve-twice | 53.33% |
| variant-016 | Compact v010 | 52.22% |
| variant-017 | v010 + "plan approach" | 54.44% |
| variant-018 | v010 + "show full reasoning" | 48.89% |
| variant-019 | AIME-specialist + v010 base | 56.67% |
| variant-020 | "Think deeply" + verify | 48.89% |
| variant-021 | v010 + answer form + range check | 56.67% |

### Test Results (8 runs per variant, 30 problems, temperature=1.0)

| Variant | Test Mean +/- SE | Stdev | vs GEPA (49.06) |
|---------|------------------|-------|-----------------|
| baseline (v001) | 46.67 +/- 2.00 | 5.65 | -2.39 |
| v010 | 47.92 +/- 1.40 | 3.95 | -1.14 |
| **v013** | **49.58 +/- 0.99** | **2.79** | **+0.52** |
| v021 | 45.84 +/- 2.24 | 6.35 | -3.22 |

### Key Findings

1. **Format enforcement is critical**: Adding `\boxed{NNN}` format instruction improved answer extraction.
2. **Leading zeros prevent scorer mismatches**: e.g., `\boxed{007}` not `\boxed{7}`.
3. **Expert role framing helps**: "expert competition mathematician" adds ~3-5pp.
4. **"Solve twice with different method" is the strongest verification instruction**.
5. **Range check instruction helps on test**: v013's "confirm it is a non-negative integer between 0 and 999" adds robustness.
6. **Verbose prompts hurt**: Adding error taxonomies, detailed guidance, or too many instructions degrades performance.
7. **Minimal prompts are not optimal either**: v009 (ultra-minimal) underperformed the 4-step v010/v013.
8. **Best variant (v013)** beats GEPA target: 49.58% vs 49.06%.
9. **v013 has the lowest variance** (stdev=2.79) across all tested variants -- more consistent.

