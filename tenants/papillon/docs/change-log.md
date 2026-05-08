<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-05-08 — Initial scaffold
- Summary: Created Papillon tenant mirroring GEPA's `Papillon` splits (111 train / 111 val / 221 test). 3-node redact-then-respond chain, composite scorer combining LLM-judged quality and literal-PII leakage.
- Why: Required for FEPO vs GEPA head-to-head comparison on privacy-preserving request rewriting.
- Files/configs: Full directory scaffold — chain (`chains/papillon.py`), scorer (`code/scorers/papillon_scorer.py`), 4 baseline prompts (craft / untrusted / respond / judge), configs, 8 required docs, tests, committed dataset + fingerprint.
- Eval impact: None yet — scaffold and baseline only.
- Rollback notes: Remove `tenants/papillon/` directory; remove the 3 allow-list exceptions for `tenants/papillon/datasets/datasets/` from root `.gitignore`.
