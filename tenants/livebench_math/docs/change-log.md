<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-05-12 — Initial Setup
- Summary: Tenant scaffold created with baseline variant-001 prompt.
- Config: gpt-4.1-mini, temperature=1.0, top_p=0.95, 1-node CoT chain.
- Target: 64% composite score on val split.

## 2026-05-12 — Scorer Fix (AMPS_Hard)
- Bug: `run_with_timeout()` in AMPS_Hard scorer used `multiprocessing.Process` which failed
  to pickle a local closure. All 52 AMPS_Hard cases scored 0% due to SymPy comparison errors.
- Fix: Replaced `multiprocessing.Process` with `threading.Thread` in
  `tenants/livebench_math/code/scoring_utils/AMPS_Hard/utils.py`.
- Impact: AMPS_Hard went from 0% → 36.5% on val split.
- Also fixed `score_breakdown` to return only numeric values (moved task/subtask/feedback to metadata).

## 2026-05-12 — Prompt Renderer Fix (ROOT CAUSE)
- Bug: `_replace_placeholders()` in `src/hephaestus/engine/prompt_renderer.py` used a
  while-loop that rescanned substituted text. Questions with LaTeX set notation like
  `${-22, 22, 11}$` were consumed as placeholders, stripping data from the rendered prompt.
  20/52 AMPS_Hard cases received truncated questions → model correctly said "data missing".
- Fix: Changed `_replace_placeholders()` to single-pass, only replacing valid identifier
  patterns (alphanumeric + underscore + hyphen). Non-identifier `${...}` patterns are preserved.
- Impact: AMPS_Hard went from 36.5% → 67.3%. Overall val score: 71.96%.
