<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- `redact_query`: Output a version of the query with all PII replaced by placeholders.
- `reconstruct_response`: Output a complete, helpful response to the original query.

## Variant Strategy
- Variants in `prompts/modules/{redact_query,reconstruct_response}/variant-NNN.md`.
- Optimization targets better PII identification and reconstruction quality.

## Non-Goals
- Untrusted LLM prompt optimization (fixed system).
- PII detection model training.
