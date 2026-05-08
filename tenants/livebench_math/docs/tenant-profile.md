<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
- LiveBench-Math tenant based on HuggingFace `livebench/math`.
- Mirrors the GEPA paper's (arXiv:2507.19457) `LiveBenchMathBench` — a mix of AMC/SMC, AIME, IMO/USAMO, and AMPS_Hard problems.

## Security Environment Assumptions
- Inputs are publicly available math competition problems.
- No retrieval; a single LLM call produces an answer in a format dictated by the question type.

## Threat Model Focus
- Evaluation correctness: scores computed via the task-dispatching metric from LiveBench (`calculate_livebench_score`).
- Parse robustness: answers must be extractable by GEPA's scoring utilities for each of 5 task families.

## Known Safe Patterns
- All questions have a `ground_truth` field used by the scorer.
- Task type dispatched on `question_d["task"]` / `question_d["subtask"]` — 5 families supported.

## Tenant Terminology
- "AMPS_Hard": a hard synthetic math problem family from the AMPS benchmark.
- "Proof rearrangement": IMO/USAMO-style task using string-edit-distance partial-credit scoring.
- "LiveBench": the public benchmark whose `math` split this tenant mirrors via GEPA's `LiveBenchMathBench`.
