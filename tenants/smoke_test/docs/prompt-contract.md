<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- The model must output exactly one word: `yes` or `no`.
- No additional text, punctuation, or explanation.

## Decision Policy
- Answer the question truthfully with "yes" or "no".
- Questions are trivially easy — the model should not overthink.

## Defang and Safety Rules
- No defanging needed — inputs are plain-text factual questions.
- No PII or sensitive data in the dataset.

## Variant Strategy
- Variants stored in `prompts/variants/variant-NNN.md`.
- `variant-001.md`: no format constraint (known-bad — produces verbose answers).
- `variant-002.md`: strict "yes or no" constraint (known-good baseline).

## Non-Goals
- Domain-specific reasoning or few-shot examples.
- Multi-word or explanatory answers.
- Prompt optimization beyond what is needed for pipeline validation.
