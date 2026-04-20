<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-03-19 — Variant-003 (all modules optimized)

- Summary: Comprehensive prompt rewrite across all 4 LLM modules. Added task-specific instructions, answer format constraints, anti-"unknown" rules, and improved summarization guidance.
- Why: Baseline DSPy-format prompts had no task-specific instructions, leading to verbose answers that failed EM, and models that gave up when retrieval was incomplete.
- Changes:
  - `generate_answer/variant-003.md`: Strong answer brevity rules, must-always-answer rule, singular form guidance, comparison question handling.
  - `summarize1/variant-003.md`: Extract all potentially relevant facts, never say "no relevant information found", preserve exact spellings.
  - `summarize2/variant-003.md`: Same improvements as summarize1, plus guidance on combining information across hops.
  - `generate_query_with_context/variant-002.md`: Entity-focused search query generation, keyword-rich queries, avoid repeating original question.
- Config: `remote-chain-variant003-train.json` / `remote-chain-variant003-val.json`

### Variant-003 scores:
| Split | EM | F1 | Delta vs Baseline |
|-------|------|------|------|
| Train (150) | 80.00 | 84.66 | +39.33 |
| Val (300) | 70.33 | 77.48 | +31.00 |
| Test (300, 3 runs) | 72.67 ±0.33 | 78.84 ±0.34 | +38.00 |

Test run breakdown: 72.33, 72.67, 73.00 EM (very low variance at temp=1.0).

### Intermediate: Variant-002 scores:
| Split | EM | F1 | Delta vs Baseline |
|-------|------|------|------|
| Train (150) | 74.67 | 80.21 | +34.00 |
| Val (300) | 65.67 | 72.98 | +26.34 |

---

## 2026-03-05 — Baseline
- Summary: GEPA-aligned chain with all variant-001 prompts.
- Why: Aligned chain with GEPA paper's HoVerMultiHop program. 9-node to 6-node chain (removed query_hop1, alias_hop1, alias_hop2); split summarize into summarize1/summarize2; ColBERT k=7; temperature=1.0; pure EM scoring.
- Config: gpt-4.1-mini, temperature=1.0, top_p=0.95, ColBERT k=7, 6-node GEPA chain.

### Baseline scores (all variant-001):
| Split | EM | F1 |
|-------|------|------|
| Train (150) | 40.67 | 51.73 |
| Val (300) | 39.33 | 53.28 |
| Test (300) | 34.67 | 49.05 |

---

## 2026-03-02
- Summary: Initial tenant scaffold created.
- Why: Set up HotpotQA tenant structure for GEPA pipeline replication.
- Files/configs: Full directory scaffold, docs, README.
- Eval impact: None yet — scaffold only.
- Rollback notes: Remove `tenants/hotpotqa/` directory.
