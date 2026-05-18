<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- `redact_query`: Output a version of the query with all PII replaced by placeholders.
- `reconstruct_response`: Output a complete, helpful response to the original query.

## Decision Policy
- The chain follows a fixed pipeline: redact → query untrusted LLM → reconstruct.
- The trusted LLM handles both redaction and reconstruction.

## Defang and Safety Rules
- PII must never appear in the redacted query sent to the untrusted model.
- Placeholder format must be consistent between redaction and reconstruction steps.

## Variant Strategy
- Variants in `prompts/modules/{redact_query,reconstruct_response}/variant-NNN.md`.
- Optimization targets better PII identification and reconstruction quality.

## Non-Goals
- Untrusted LLM prompt optimization (fixed system).
- PII detection model training.
