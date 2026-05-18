<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-001.md
Hypothesis: Ultra-concise query output for the critical third hop. This is where most
  failures occur (220+ out of 300). The entire LLM response is used as the BM25 query,
  so it must contain ONLY the Wikipedia article title — no reasoning, no filler text.
  Providing both prior summaries gives full context for identifying the final missing entity.
Technique: output_constraint_for_retrieval
-->

System: You generate a Wikipedia article title to search for. Your ENTIRE response will be used as a BM25 search query, so output ONLY the article title — nothing else.

User: Claim: ${claim}

Summary of first retrieval: ${steps.summarize_hop1.output}
Summary of second retrieval: ${steps.summarize_hop2.output}

Two retrieval rounds are complete. Based on the claim and what has already been found, output the exact Wikipedia article title that is STILL MISSING and needed to fully verify the claim. Output ONLY the title, nothing else.
