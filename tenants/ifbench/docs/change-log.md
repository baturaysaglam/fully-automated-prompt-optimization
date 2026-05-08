<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-05-08 — Initial scaffold
- Summary: Created IFBench tenant mirroring GEPA's `IFBench` splits (150 train / 300 val / 294 test), 2-node draft-then-revise chain, instruction-pass-rate scorer that delegates to `instructions_registry.INSTRUCTION_DICT` from gepa-artifact.
- Why: Required for FEPO vs GEPA head-to-head comparison on instruction-following.
- Files/configs: Full directory scaffold — chain (`chains/two_stage.py`), scorer (`code/scorers/ifbench_scorer.py`), 2 baseline prompts, configs, 8 required docs, tests, committed dataset + fingerprint.
- Eval impact: None yet — scaffold and baseline only.
- Rollback notes: Remove `tenants/ifbench/` directory; remove the 3 allow-list exceptions for `tenants/ifbench/datasets/datasets/` from root `.gitignore`.
