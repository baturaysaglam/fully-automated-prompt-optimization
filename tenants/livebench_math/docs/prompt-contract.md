<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- The `solve` LLM node produces a single answer embedded in its output.
- The scorer delegates to `calculate_livebench_score` which handles per-family answer extraction (e.g., `\boxed{…}`, `Answer: …`, proof structure), so the prompt does not need to enforce one specific format.

## Decision Policy
- The chain has a single node: no branching, no retrieval, no retry/verification.

## Defang and Safety Rules
- No defanging required — all problems are public math competition text.

## Variant Strategy
- Prompt templates live in `prompts/modules/solve/variant-NNN.md`.
- Seed prompt (variant-001) uses a minimal DSPy-style signature scaffold matching GEPA's `program_cot` ("Solve the question and provide the answer in the correct format.").
- Per-module optimization creates new variants.

## Non-Goals
- Prompt templates do not compute per-family answer extraction — that is scorer logic inside `calculate_livebench_score`.
- Prompt templates do not detect task type — the scorer reads `question_d["task"]` from metadata.
