<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- The model should produce step-by-step reasoning followed by a final integer answer.
- Preferred format: `\boxed{N}` where N is the integer answer.
- The scorer extracts `\boxed{N}` first, falls back to the last integer in output.

## Decision Policy
- The model should solve the problem step by step, showing all work.
- Final answer must be a non-negative integer in [0, 999].
- When uncertain, the model should verify its answer by checking against constraints.

## Defang and Safety Rules
- No defanging needed — inputs are math competition problems with no sensitive content.
- No PII or sensitive data in the dataset.

## Variant Strategy
- Variants stored in `prompts/variants/variant-NNN.md`.
- `variant-001.md`: CoT baseline from ETGPO paper ("Please think step by step and then solve the task.").
- Subsequent variants append error-taxonomy guidance targeting common failure modes.

## Non-Goals
- Proof generation or formal verification.
- Multiple-choice answer selection.
- Generating problem statements.
