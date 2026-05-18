<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-05-14 — K8s Validation (Target Met)
- Summary: Ran baseline (variant-001) and two new prompt variants on K8s (val split, 300 cases).
- Config: gpt-4.1-mini, temperature=0.0, BM25 k=7/7/10.
- Results:
  - variant-001 (baseline): **partial_recall=61.44%** — meets >=60% target
  - variant-015 (structured output + gap analysis): partial_recall=60.44%
  - variant-016 (CoT entity tracking): partial_recall=57.56%
- Conclusion: Baseline meets target. CoT-heavy prompts hurt BM25 query quality (retrieval node passes full LLM output as BM25 query).
- K8s infra: BM25 corpus requires ~5GB RAM; required 20Gi limit pod on node 4mbg.

## 2026-05-12 — Initial Setup
- Summary: Tenant scaffold with 3-hop retrieval chain, BM25 from hotpotqa.
- Config: gpt-4.1-mini, temperature=1.0, BM25 k=7/7/10 across hops.
- Target: 62% binary retrieval recall on val split.

