<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- `summarize1` and `summarize2` produce a concise summary of the retrieved passages.
- `create_query_hop2` and `create_query_hop3` produce a single search query string targeting the next retrieval hop.
- No LLM node produces an answer — the scorer reads directly from the 3 retrieval node outputs.

## Decision Policy
- The chain has a fixed 3-hop retrieval pattern with no branching.
- Hop 1 retrieves using the raw claim (no query-gen LLM call).
- Hops 2 and 3 generate follow-up queries via LLM, then retrieve.

## Defang and Safety Rules
- No defanging required — claims are public Wikipedia-derived text.

## Variant Strategy
- Prompt templates live in `prompts/modules/<module_name>/variant-NNN.md`.
- Seed prompts (variant-001) use DSPy-style signature scaffolding matching GEPA's ChainOfThought programs for `claim,passages->summary`, `claim,summary_1->query`, etc.
- Per-module optimization creates new variants via the optimization skill.

## Non-Goals
- Prompt templates do not perform retrieval — that is handled by the retrieval nodes.
- Prompt templates do not score retrieval quality — that is scorer logic.
- Prompt templates do not produce a verdict label — `hoverBench` is retrieval-only.
