<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Global reference: `docs/processes/prompt-iteration-loop.md`
- Single-node answer chain (`chains/answer.py`) with exact-match scorer.
- `variant-002` is the known-good baseline (strict "yes or no" constraint).

## Iteration Loop
1. Follow the global loop in `docs/processes/prompt-iteration-loop.md`.
2. This tenant uses trivially easy yes/no questions — prompt changes should keep the strict output format constraint that makes exact-match work.
3. Do not add domain-specific reasoning or few-shot examples — the questions are intentionally simple.

## Scope Constraint
- Prompt changes: modify prompt variant files (`prompts/variants/variant-*.md`).
- Do not change the scorer.

## Chain-Level Optimization Scope

The optimization agent reads this section to determine allowed optimization levels.

- **Structural changes**: In-scope. The single-node answer chain can be extended with additional steps (e.g., self-refine, verification). Chain variants go in `chains/variants/` following `docs/processes/chain-variant-conventions.md`.
- **Parameter changes**: In-scope. Model settings (`temperature`, `max_tokens`) may be adjusted via eval config overrides.
- **Prompt changes**: In-scope. Follow standard prompt variant conventions.
- **Allowed patterns**: self-refine, chain-of-thought verification. Other patterns from `agentic-chain-patterns.md` require user approval.
- **Constraints**: Output must remain a single word ("yes" or "no") for exact-match scoring. Any new chain steps must preserve this output format.

## Stop Criteria
- 100% exact_match on all cases.

## Regression Prevention
- Always verify exact-match still passes on the full dataset after any prompt change.
- `variant-001` (verbose, no format constraint) exists as a known-bad reference — do not regress to that pattern.

## Lessons Logging
- Record iteration outcomes in `docs/change-log.md`.
