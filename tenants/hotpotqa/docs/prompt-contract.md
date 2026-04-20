<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- All LLM nodes produce plain text output.
- `generate_query_with_context` produces a single search query string (hop 2 only; hop 1 uses the raw question directly).
- `summarize1` produces a concise passage summary for hop 1.
- `summarize2` produces a concise passage summary for hop 2, integrating the prior summary.
- `generate_answer` produces a short factoid answer string.

## Decision Policy
- The chain follows a fixed 2-hop retrieval pattern: no branching or conditional logic.
- The final answer node synthesizes from both hop summaries.

## Defang and Safety Rules
- No special defanging required — inputs and outputs are factoid QA text.

## Variant Strategy
- Prompt templates live in `prompts/modules/<module_name>/variant-NNN.md`.
- Seed prompts (variant-001) use minimal DSPy-style instructions for GEPA optimization baseline.
- Per-step optimization creates new variants via the prompt iteration skill.

## Non-Goals
- Prompt templates do not handle retrieval logic (that is a module node).
- Templates do not perform answer normalization (that is scorer logic).
