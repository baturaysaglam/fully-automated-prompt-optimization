<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

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
