<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
AIME 2025 is a public benchmark tenant for evaluating LLM mathematical reasoning
and prompt optimization methods. Based on the American Invitational Mathematics
Examination (AIME), a challenging high-school math competition. Setup follows
ETGPO (arxiv 2602.00997) for direct comparison with GEPA, MIPROv2, and ETGPO.

## Security Environment Assumptions
- Input: LaTeX-formatted math problem statements from public competition archives.
- Output: a single integer in [0, 999].
- No access to external tools, calculators, or databases during inference.

## Threat Model Focus
- Primary challenge: multi-step mathematical reasoning across algebra, geometry,
  number theory, and combinatorics.
- Common failure modes: algebraic calculation errors, incorrect generalization
  from patterns, misinterpretation of problem constraints.

## Known Safe Patterns
- All answers are non-negative integers in [0, 999].
- Problem statements are publicly available competition problems.

## Tenant Terminology
- **AIME**: American Invitational Mathematics Examination.
- **CoT**: Chain of Thought — step-by-step reasoning prompting.
- **GEPA**: Genetic Evolution of Prompts and Agents (Agrawal et al., 2025).
- **ETGPO**: Error Taxonomy-Guided Prompt Optimization (Singh et al., 2026).
