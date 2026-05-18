<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- The model should produce step-by-step reasoning followed by a final answer.
- AMC/SMC: repeat the letter 5 times (e.g., "CCCCC") or use `\boxed{C}`.
- AIME: integer in the last 50 characters or `\boxed{N}`.
- Olympiad: comma-separated integer sequence after "answer:".
- AMPS Hard: LaTeX expression in `\boxed{...}`.

## Decision Policy
- The model should solve the problem step by step, showing all work.
- For multiple choice, verify by substituting back.
- For symbolic answers, simplify to canonical form.

## Defang and Safety Rules
- No defanging needed — inputs are math problems with no sensitive content.
- No PII or sensitive data in the dataset.

## Variant Strategy
- Variants stored in `prompts/variants/variant-NNN.md`.
- `variant-001.md`: Minimal CoT baseline ("Please think step by step and then solve the task.").
- Subsequent variants will target domain-specific formatting guidance.

## Non-Goals
- Formal proof generation.
- Code generation for computation.
- Multi-turn dialogue.
