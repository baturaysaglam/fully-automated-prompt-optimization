<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
- Instruction-following tenant based on Allen AI's IFBench.
- Mirrors the GEPA paper's (arXiv:2507.19457) `IFBench` — evaluates whether a model's response obeys explicit format / count / structure constraints embedded in the prompt.

## Security Environment Assumptions
- Inputs are public IFBench prompts with well-defined constraints (word counts, keyword counts, letter limits, etc.).
- All instruction evaluators are pure-Python (no external network calls beyond the LLM nodes in the chain itself).

## Threat Model Focus
- Correctness of constraint checking: the scorer delegates to `instructions_registry.INSTRUCTION_DICT` from the gepa-artifact repo.
- Pipeline fidelity: the 2-node chain must mirror GEPA's `IFBenchCoT2StageProgram`.

## Known Safe Patterns
- Each case specifies an ordered `instruction_id_list` + aligned `kwargs` list.
- Pass rate is the fraction of instructions satisfied by any of 8 response variants (original, asterisk-stripped, first/last line dropped).

## Tenant Terminology
- "Instruction id": a string key into `INSTRUCTION_DICT` that names a constraint family (e.g., `count:word_count_range`).
- "Variant response": the scorer tests 8 lightly modified versions of the model output; a pass on any counts as success.
- "Two-stage": the chain produces a draft then a revised response.
