<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-015.md
Hypothesis: For the critical third hop (highest failure rate), use the same ultra-concise
  output constraint but with slightly different framing emphasizing the "last missing piece."
  The model must identify the ONE remaining entity not found in two prior rounds.
Technique: constrained_output_with_emphasis
-->

System: You identify the final Wikipedia article to search for. Your ENTIRE response is used as a BM25 search query. Output ONLY the Wikipedia article title — no explanation, no quotes, no extra text.

User: Claim: ${claim}

Summary of first retrieval: ${steps.summarize_hop1.output}
Summary of second retrieval: ${steps.summarize_hop2.output}

After two retrieval rounds, one entity from the claim is still missing. What is it? Output ONLY its Wikipedia article title.
