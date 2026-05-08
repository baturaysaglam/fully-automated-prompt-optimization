<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
- Privacy-preserving request rewriting tenant using Columbia-NLP's PUPA dataset.
- Mirrors the GEPA paper's (arXiv:2507.19457) `Papillon` benchmark — evaluate the ability to redact private information from a user query and still produce a high-quality response.

## Security Environment Assumptions
- Inputs are real user queries from PUPA with PII annotated by Presidio (phone numbers, emails, persons, URLs) and organization names.
- The "untrusted LLM" node represents an external, untrusted API surface; its input (the redacted request) must not leak PII.

## Threat Model Focus
- Leakage: any gold PII unit appearing literally in the redacted request is a failure.
- Utility: the final response must be at least as good as the gold target (LLM-judged).

## Known Safe Patterns
- `pii_units` contains Presidio-generated placeholders (e.g., `presidio_anonymized_person`) as well as concrete organization names — all are treated as private.
- All three splits are hardcoded at 111 / 111 / 221; no random sampling.

## Tenant Terminology
- "PUPA" / "pupa_new": the HuggingFace dataset configuration this tenant consumes.
- "Redacted request": the intermediate output of `craft_redacted_request` — the string scored for leakage.
- "Untrusted LLM": the middle chain node modelling an external LLM API; reuses the shared FEPO provider for cost parity.
