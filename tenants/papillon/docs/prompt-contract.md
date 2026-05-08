<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- `craft_redacted_request` produces a single redacted query suitable for an untrusted LLM.
- `untrusted_llm` produces a response to the redacted request.
- `respond_to_query` produces the final response to the user, composing the untrusted answer with the original query.

## Decision Policy
- Fixed 3-node sequence: redact → untrusted answer → respond.
- No retry/verification step. The untrusted LLM is the same shared provider as the other nodes (simplification — see `docs/eval-operations.md` for the fidelity note).

## Defang and Safety Rules
- Never allow PII units from the user query to appear in the redacted request — this is the leakage signal.
- Use placeholder tokens (Presidio-style) for sensitive entities.

## Variant Strategy
- Prompt templates live in `prompts/modules/<module>/variant-NNN.md`.
- Seed prompts (variant-001) match GEPA's `CraftRedactedRequest` / `RespondToQuery` signatures (DSPy ChainOfThought/Predict).
- The `judge` module has a separate prompt (`prompts/modules/judge/variant-001.md`) used only by the scorer's quality path.
- Per-module optimization creates new variants.

## Non-Goals
- Prompt templates do not compute leakage scores — that is scorer logic.
- The `untrusted_llm` prompt does not enforce PII handling — its role is to model an untrusted external API that simply responds to whatever request it receives.
