<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-05-08 — Initial scaffold
- Summary: Created HoVer tenant mirroring GEPA's `hoverBench` splits (150 train / 300 val / 300 test), 7-node multi-hop retrieval chain, retrieval-subset scorer.
- Why: Required for FEPO vs GEPA head-to-head comparison on multi-hop claim verification.
- Files/configs: Full directory scaffold — chain (`chains/multi_hop.py`), scorer (`code/scorers/hover_scorer.py`), 4 baseline prompts, configs, 8 required docs, tests, committed dataset + fingerprint.
- Eval impact: None yet — scaffold and baseline only.
- Rollback notes: Remove `tenants/hover/` directory; also remove the 3 allow-list exceptions for `tenants/hover/datasets/datasets/` from root `.gitignore`.
