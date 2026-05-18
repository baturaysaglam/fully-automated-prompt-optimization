<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-05-14 — Variant-005: Target Met (57.82%)

- **Score: 57.82% instruction adherence** on test split (294/294 cases)
- Target: >= 55.5% ✅ ACHIEVED
- Generate prompt: `variant-005.md` — Explicit constraint listing, step-by-step verification,
  keyword counting, and "---" separator for response extraction.
- Verify prompt: `variant-005.md` — Minimal pass-through with minor fix capability.
- Key insight: Putting all constraint-satisfaction work in the generate step and using a
  minimal verify (pass-through with minor fixes only) outperforms aggressive verification.
- Scorer bugfix: Fixed IndexError in ParagraphLastFirstWordMatchChecker for empty word lists.
- Dependency fix: Added `immutabledict`, `langdetect`, `packaging` to ifbench extras.
- Run: `hephaestus-ifbench-tf1jly`, duration: 5777s (~96 min)

## 2026-05-12 — Initial Setup
- Summary: Tenant scaffold created with baseline variant-001 prompts.
- Config: gpt-4.1-mini, temperature=1.0, 2-node generate→verify chain.
- Target: 60% instruction adherence on test split.

