<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-001.md
Hypothesis: Ultra-concise query output optimized for BM25. The entire LLM response
  is used as the BM25 search query, so it must contain ONLY the Wikipedia article
  title to search for — no reasoning, no explanation, no preamble.
Technique: output_constraint_for_retrieval
-->

System: You generate a Wikipedia article title to search for. Your ENTIRE response will be used as a BM25 search query, so output ONLY the article title — nothing else.

User: Claim: ${claim}

Summary of first retrieval: ${steps.summarize_hop1.output}

Based on the claim and what has already been found, output the exact Wikipedia article title that is still needed to verify this claim. Output ONLY the title, nothing else.
