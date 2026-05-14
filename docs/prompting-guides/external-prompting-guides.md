<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# External Prompting Guides

## Purpose
Optional reference for prompting principles. Consult when a specific technique seems relevant to a failure pattern.

Related:
- For synthetic dataset construction references and quality checklist, see `docs/prompting-guides/synthetic-example-creation-sources.md`.

## Canonical Top-5 Sources
- OpenAI Prompt Engineering Guide: https://platform.openai.com/docs/guides/prompt-engineering
- Anthropic Prompt Engineering Overview: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
- Google Vertex AI Prompt Design Strategies: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/prompt-design-strategies
- Microsoft Azure OpenAI Prompt Engineering: https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/prompt-engineering
- OPRO (ICLR 2024): Large Language Models as Optimizers: https://arxiv.org/abs/2309.03409

Retrieval date for this source set: February 17, 2026.

## Unified Principles

1. **Be explicit about task and success conditions** — state the model's job and what counts as correct.
2. **Specify strict output contract** — define required sections, ordering, allowed fields, prohibited formats.
3. **Structure context with delimiters and hierarchy** — separate system rules, case context, and output instructions.
4. **Use examples strategically** — add few-shot examples only for patterns that persist after instruction clarity fixes.
5. **Define ambiguity and abstention behavior** — instruct how to handle uncertain or conflicting evidence.
6. **Break complex tasks into ordered reasoning steps** — sequence evaluation while keeping output format strict.
7. **Iterate with eval-driven loops** — baseline, eval, cluster failures, apply targeted changes, re-test.
8. **Minimize overfitting** — favor generalizable rules over one-off artifact-specific heuristics.
9. **Optimize against explicit objectives and budgets** — define targets before edits, track against them, escalate when small edits fail.

## Failure Cluster to Fix Mapping

- **Classification accuracy**: Tighten decision criteria and precedence rules. Add explicit uncertainty handling. If still unstable, add one representative few-shot example.
- **Response-shape**: Enforce exact heading names and order. Ban optional extra sections when checks require strict shape.
- **Plain-text/format**: State plain-text-only output explicitly. Ban markdown bullets, tables, fenced code blocks, and rich formatting.
- **Defang-related**: Add strict URL/IOC normalization rules and clear positive/negative examples.
- **Mixed regression after a fix**: Reduce scope of the last change. Prefer explicit rule precedence over broad rewrites.
