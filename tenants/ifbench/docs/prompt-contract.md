<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- The model should output a response that satisfies all embedded instructions.
- No specific output format required beyond following the constraints.
- The verify step rewrites the response to fix constraint violations.

## Decision Policy
- Generate step: produce initial response following instructions.
- Verify step: check response against constraints and rewrite if needed.

## Defang and Safety Rules
- No defanging needed — inputs are synthetic instruction-following tasks.
- No PII or sensitive data.

## Variant Strategy
- Variants stored in `prompts/modules/{generate,verify}/variant-NNN.md`.
- `variant-001.md`: Minimal baseline prompts.
- Subsequent variants will add constraint-awareness guidance.

## Non-Goals
- Code generation.
- Multi-turn dialogue.
- Knowledge-intensive tasks.
