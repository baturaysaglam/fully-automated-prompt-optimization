<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Iteration Playbook

## Prerequisites
- Global references:
  - `docs/processes/prompt-iteration-loop.md`
- Tenant-specific prerequisites only (required inputs, baseline variant, and skills).

## Iteration Loop
1. Follow the global iteration loop from `docs/processes/prompt-iteration-loop.md`. For automated optimization, use the `optimization` agent.
2. Document tenant-specific overrides only (dataset quirks, special checks, or escalation rules).
3. Re-run evals and iterate until tenant success criteria are met.

## Stop Criteria
- Explicit tenant-specific criteria for completion.

## Regression Prevention
- Required tenant-specific checks before accepting a variant.

## Lessons Logging
- Where and how to record lessons learned.
