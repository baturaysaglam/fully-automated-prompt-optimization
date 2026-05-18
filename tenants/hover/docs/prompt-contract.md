<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- LLM nodes generate summaries and search queries (free-form text).
- The chain's final output_text is the combined retrieval results.
- Scoring evaluates retrieval coverage, not LLM output format.

## Decision Policy
- The chain follows a fixed 3-hop retrieval pattern: no branching or conditional logic.
- Each hop generates a query, retrieves passages, and summarizes them for the next hop.

## Defang and Safety Rules
- No special defanging required — inputs are factual claims and outputs are Wikipedia passages.

## Variant Strategy
- Variants in `prompts/modules/{summarize1,summarize2,query_hop2,query_hop3}/`.
- `variant-001.md`: Baseline prompts.
- Optimization targets query generation quality for better retrieval recall.

## Non-Goals
- Claim classification (SUPPORTED/NOT SUPPORTED).
- Passage re-ranking.
- Answer generation from retrieved evidence.
