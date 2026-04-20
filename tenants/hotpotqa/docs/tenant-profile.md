<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
- Multi-hop question answering evaluation based on the HotpotQA benchmark dataset.
- Replicates the GEPA paper (arXiv:2507.19457) pipeline for prompt optimization research.

## Security Environment Assumptions
- Input data is publicly available HotpotQA fullwiki questions (hard subset).
- Retrieval uses in-process BM25 (`bm25s`) over Wikipedia abstracts.

## Threat Model Focus
- Evaluation accuracy: exact match (EM) and token-level F1 against gold answers.
- Pipeline fidelity: ensuring the multi-hop chain correctly decomposes questions across two retrieval hops.

## Known Safe Patterns
- Gold answers are short factoid strings (names, dates, yes/no).
- BM25 retrieval returns Wikipedia abstract passages that are public domain.

## Tenant Terminology
- "Hop": one cycle of query generation, retrieval, and summarization.
- "GEPA": Generalized Evolutionary Prompt Architect — the paper whose pipeline this tenant replicates.
- "Module": one of the three prompt templates used by LLM nodes (generate_query_with_context, summarize1, summarize2) plus generate_answer.
