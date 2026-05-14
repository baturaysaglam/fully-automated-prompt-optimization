<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
Papillon (PUPA) is a privacy-preserving prompting benchmark. Evaluates whether
a system can redact PII from queries, obtain useful responses from an untrusted
LLM, and reconstruct accurate answers — all while preventing PII leakage.
Setup follows GEPA (arXiv:2507.19457).

## Security Environment Assumptions
- Input: Queries containing PII (names, addresses, etc.).
- Trusted LLM: performs redaction and reconstruction.
- Untrusted LLM: receives only the redacted query.
- Output: Reconstructed response with full utility.

## Threat Model Focus
- Primary challenge: balancing privacy (no PII leakage) with response quality.
- Common failure modes: incomplete PII redaction, quality loss during reconstruction.

## Tenant Terminology
- **PII**: Personally Identifiable Information.
- **PUPA**: Privacy-Utility Preserving Approach.
- **Leakage**: Fraction of PII units found in the redacted query.
- **Quality**: LLM-as-judge bidirectional comparison against target response.
