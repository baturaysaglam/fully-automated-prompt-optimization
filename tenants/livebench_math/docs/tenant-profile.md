<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
LiveBench Math is a public benchmark tenant for evaluating LLM mathematical
reasoning across multiple domains: math competitions (AMC, SMC, AIME), olympiad
proofs (IMO, USAMO), and symbolic computation (AMPS Hard). Setup follows GEPA
(arXiv:2507.19457) for direct comparison.

## Security Environment Assumptions
- Input: Math problems from LiveBench including LaTeX, multiple choice, and
  symbolic expressions.
- Output: Task-dependent — single letter (A-E), integer, sequence of integers,
  or symbolic expression.
- No access to external tools, calculators, or CAS during inference.

## Threat Model Focus
- Primary challenge: multi-domain math reasoning with heterogeneous output formats.
- Common failure modes: incorrect LaTeX formatting, wrong answer extraction for
  multi-choice, algebraic errors, timeout on symbolic comparison.

## Known Safe Patterns
- All problems are from public math competitions or synthetic datasets.
- No PII or sensitive data.

## Tenant Terminology
- **AMC/SMC**: American/Swedish Mathematics Competition (multiple choice A-E).
- **AIME**: American Invitational Mathematics Examination (integer 0-999).
- **IMO/USAMO**: International/US Math Olympiad (proof rearrangement).
- **AMPS Hard**: Symbolic math problems requiring CAS equivalence checking.
- **GEPA**: Genetic Evolution of Prompts and Agents (Agrawal et al., 2025).
