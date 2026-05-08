<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-05-08 — Initial scaffold
- Summary: Created LiveBench-Math tenant mirroring GEPA's `LiveBenchMathBench` splits (121 train / 121 val / 126 test). Scorer wraps `calculate_livebench_score` from the GEPA artifact via runtime import.
- Why: Required for FEPO vs GEPA head-to-head comparison on math reasoning tasks across 5 task families (AMC/SMC, AIME, IMO/USAMO, AMPS_Hard).
- Files/configs: Full directory scaffold — chain (`chains/cot.py`), scorer (`code/scorers/livebench_math_scorer.py`), baseline prompt (`prompts/modules/solve/variant-001.md`), configs, 8 required docs, tests, committed dataset + fingerprint.
- Eval impact: None yet — scaffold and baseline only.
- Rollback notes: Remove `tenants/livebench_math/` directory; remove the 3 allow-list exceptions for `tenants/livebench_math/datasets/datasets/` from root `.gitignore`.
