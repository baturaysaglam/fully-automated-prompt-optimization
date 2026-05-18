<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-015.md
Hypothesis: Add a brief reasoning step before committing to the query, while keeping
  the final output strictly to the entity name. The model reasons about what's missing,
  then outputs ONLY the search term on the final line. Since the entire output goes to
  BM25, we instruct it to emit ONLY the search query.
Technique: constrained_reasoning_then_output
-->

System: You identify the next Wikipedia article to search for. Your ENTIRE response is used as a BM25 search query. Output ONLY the Wikipedia article title to search — no explanation, no quotes, no punctuation beyond what's in the title.

User: Claim: ${claim}

Summary of first retrieval: ${steps.summarize_hop1.output}

What entity from the claim has NOT been found yet? Output its Wikipedia article title and nothing else.
