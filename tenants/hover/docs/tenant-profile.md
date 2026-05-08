<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
- Claim-verification retrieval tenant based on the HoVer dataset (3-hop subset).
- Mirrors the GEPA paper's (arXiv:2507.19457) `hoverBench` — retrieves evidence documents that support or refute a natural-language claim.

## Security Environment Assumptions
- Inputs are publicly available HoVer claims; no PII.
- Retrieval uses shared in-process BM25 (`bm25s`) over Wikipedia abstracts (`wiki.abstracts.2017`), pulled from `tenants/hotpotqa/data/bm25/`.

## Threat Model Focus
- Retrieval correctness: binary check for whether all gold supporting-fact titles were retrieved across 3 hops.
- Pipeline fidelity: the 7-node chain must mirror GEPA's `HoverMultiHop` in structure and k-values.

## Known Safe Patterns
- Gold supporting facts reference Wikipedia article titles that exist in the 2017 abstracts corpus.
- All examples have exactly 3 unique source documents (enforced at build time).

## Tenant Terminology
- "Hop": one cycle of query-gen + retrieval (hops 2 and 3) or direct claim retrieval (hop 1).
- "GEPA": the paper whose `hoverBench` this tenant mirrors.
- "Supporting fact": a `{key: title, value: sentence_id}` record indicating which Wikipedia article contains the evidence.
