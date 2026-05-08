<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- The `solve` LLM node produces a single integer answer embedded in its output.
- The scorer extracts the last `\\boxed{N}`, else the last `[[ ## answer ## ]] N`, else the last bare integer.
- Any reasoning text before the answer is permitted and is not scored.

## Decision Policy
- The chain has a single node: no branching, no retrieval, no retry/verification.
- The final answer is the output of `solve`.

## Defang and Safety Rules
- No defanging required — all inputs and outputs are public math problem text.

## Variant Strategy
- Prompt templates live in `prompts/modules/solve/variant-NNN.md`.
- Seed prompt (variant-001) uses a minimal DSPy-style signature scaffold matching GEPA's `program_cot` ("Solve the problem and provide the answer in the correct format.").
- Per-module optimization creates new variants via the optimization skill.

## Non-Goals
- Prompt templates do not compute or normalize the answer — that is scorer logic.
- Prompts do not request a specific output format beyond "integer answer"; answer parsing is robust to several formats.
