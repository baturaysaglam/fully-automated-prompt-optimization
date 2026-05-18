<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Optimization Loop

## Purpose

Architecture reference for the optimization system. The `optimization` agent drives the loop autonomously; this document describes the components it uses.

## Architecture

### Orchestrator

| Component | File | Role |
|-----------|------|------|
| Optimization Agent | `.claude/agents/optimization.md` | Goal-oriented optimizer — analyzes results, creates variants, runs evals, iterates until targets are met |

### Execution Components

| Component | File | Role |
|-----------|------|------|
| Variant Reviewer | `.claude/agents/variant-reviewer.md` | Independent guardrail check on proposed variants before eval |
| Eval Runner | `.claude/commands/eval-runner.md` | Runs evaluations and returns score summaries |

### Data Tools

| Component | File | Role |
|-----------|------|------|
| Synthetic Samples | `.claude/commands/synthetic-samples.md` | Creates synthetic examples for dataset augmentation |
| Synthetic Pruner | `.claude/commands/synthetic-pruner.md` | Validates and cleans synthetic data |

## Iteration Memory

Structured history lives in `tenants/<tenant_id>/docs/iteration-memory.jsonl` (one JSON record per cycle). The human-readable `change-log.md` sits alongside it. Together they give the agent cross-cycle awareness — distinguishing persistent vs new failures and avoiding re-proposing reverted approaches.

## Tenant Playbooks

Each tenant defines its own constraints in `tenants/<tenant_id>/docs/iteration-playbook.md`. Playbooks are authoritative — they set scope, success criteria, and rules that the optimization agent must follow.

## Scope Constraints

Tenant playbooks can restrict which files the optimization agent is allowed to create or modify. The mechanism has three layers:

1. **Playbook definition**: the tenant playbook includes a `### Scope Constraint` section with an `**Allowed pattern**` glob and a list of forbidden categories.
2. **Optimization agent self-check**: on startup, the agent extracts the scope constraint and verifies every file it creates or modifies against the allowed pattern before proceeding. Violations are blocking.
3. **Variant reviewer validation**: the variant-reviewer independently reads the playbook, extracts the same constraint, and verifies the variant path and any other modified files as Check 7 (Scope Compliance). This catches anything the optimization agent missed.

**Exempt operational files**: eval configs, iteration memory (`iteration-memory.jsonl`), and change logs (`change-log.md`) are not subject to scope constraints — they are necessary for the optimization loop itself.

If no `### Scope Constraint` section exists in a tenant playbook, no scope restrictions are enforced.

## Experimental Constants

Fixed for GEPA-comparison fairness (from Appendix A.4 of the GEPA paper):

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `temperature` | 1.0 | GEPA reports all GPT-4.1-mini results at temperature=1.0 |
| `top_p` | 0.95 | Matches GEPA experimental setup |
| `model` | gpt-4.1-mini | Primary task model for all tenants |
| `max_tokens` | 16000 | Matches GEPA context budget |

These are NOT tunable parameters. Tenant playbooks and the optimization agent must treat them as immutable. Altering temperature would confound prompt-quality improvements with sampling-regime changes, invalidating the comparison.

## Manual Fallback

When agents are unavailable:
1. Clone a new variant from the latest — never edit in-place.
2. Make targeted changes tied to identified failure clusters.
3. Re-run evals after each edit set and compare against baseline.
4. Keep changes with measured net improvement; revert or narrow scope otherwise.
