<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-05-08 — Initial scaffold
- Summary: Created AIME tenant mirroring GEPA's `AIMEBench` splits (45 train / 45 val / 150 test).
- Why: Required for FEPO vs GEPA head-to-head comparison on AIME problems. Independent of the sibling `aime2025` tenant (ETGPO comparison).
- Files/configs: Full directory scaffold — chain (`chains/cot.py`), scorer (`code/scorers/aime_scorer.py`), baseline prompt (`prompts/modules/solve/variant-001.md`), configs, 8 required docs, tests, committed dataset + fingerprint.
- Eval impact: None yet — scaffold and baseline only.
- Rollback notes: Remove `tenants/aime/` directory; also remove the 3 allow-list exceptions for `tenants/aime/datasets/datasets/` from root `.gitignore`.
