<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
IFBench is a public benchmark for evaluating LLM instruction following across
diverse constraint types (word count, formatting, structure, repetition, etc.).
Uses a 2-stage generate-then-verify chain. Setup follows GEPA (arXiv:2507.19457).

## Security Environment Assumptions
- Input: Natural language prompts with embedded instruction constraints.
- Output: Free-form text responses adhering to specified constraints.
- No external tool access during inference.

## Threat Model Focus
- Primary challenge: satisfying multiple simultaneous formatting/structural
  constraints while maintaining coherent content.
- Common failure modes: constraint violations in formatting (bullets, indentation),
  count constraints (word/sentence limits), and structural constraints (palindromes,
  specific character patterns).

## Known Safe Patterns
- All prompts are synthetic instruction-following tasks.
- No PII or sensitive data.

## Tenant Terminology
- **IFBench**: Instruction Following Benchmark.
- **IFEval**: Google's Instruction Following Eval (subset of instructions).
- **Instruction ID**: Unique identifier for each constraint type (e.g., "count:word_count_range").
- **GEPA**: Genetic Evolution of Prompts and Agents (Agrawal et al., 2025).
