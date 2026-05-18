<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
HoVer is a public benchmark for multi-hop claim verification via evidence
retrieval from Wikipedia. Evaluates whether a model can retrieve all relevant
supporting documents across 3 reasoning hops. Setup follows GEPA (arXiv:2507.19457).

## Security Environment Assumptions
- Input: Claims requiring multi-hop reasoning to verify.
- Output: Retrieved passages from Wikipedia abstracts corpus.
- Uses BM25 retrieval over wiki.abstracts.2017 corpus (same as hotpotqa).

## Threat Model Focus
- Primary challenge: retrieving all relevant supporting documents across 3 hops.
- Common failure modes: query generation that misses entities, retrieval recall
  on disambiguation-heavy titles.

## Tenant Terminology
- **HoVer**: Hover (Many-Hop Fact Verification).
- **BM25**: Best Match 25 — probabilistic ranking function for retrieval.
- **Supporting titles**: Gold Wikipedia article titles that contain evidence for the claim.
- **GEPA**: Genetic Evolution of Prompts and Agents (Agrawal et al., 2025).
