<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- `generate_response` produces an initial response to the user prompt (plain text).
- `ensure_correct_response` produces a revised response meant to satisfy all constraints; its output is what the scorer evaluates.
- Constraint checks run against 8 lightly normalized variants of the final response (asterisk-stripped, first/last line dropped).

## Decision Policy
- Fixed 2-node sequence: draft → revise.
- No retry/verification beyond the single revision step.

## Defang and Safety Rules
- No defanging required — prompts are public IFBench text.

## Variant Strategy
- Prompt templates live in `prompts/modules/<module>/variant-NNN.md`.
- Seed prompts (variant-001) match GEPA's `GenerateResponse` / `EnsureCorrectResponse` signatures.
- Per-module optimization creates new variants.

## Non-Goals
- Prompt templates do not implement instruction checking — that is scorer logic in `instructions_registry`.
- Prompt templates should not enumerate the full taxonomy of possible constraints; the model is expected to parse the constraints from the prompt text.
