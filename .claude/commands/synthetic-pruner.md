<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

---
description: >
  Prune noncompliant synthetic examples and normalize placeholder data.
  TRIGGER when: user wants to clean up synthetic examples, remove bad samples, fix placeholder hashes, validate synthetic data quality, or align review CSVs.
  DO NOT TRIGGER when: user is creating new synthetic examples (use synthetic-samples), running evals (use eval-runner), or optimizing prompts (use optimization agent).
---

# Synthetic Pruner

## Overview
Prune noncompliant synthetic examples and normalize placeholder hashes while keeping review CSVs aligned to the remaining example directories.

## Workflow
1. Review requirements
   - Use tenant-specific dataset requirements plus `docs/references/synthetic-requirements.md`.
2. Identify severe violations
   - Example default rule: email bodies with `<= 10` words and no greeting/signature are severe violations.
   - Missing-body examples can be kept when intentionally included as hard cases.
   - Placeholder hashes like repeated `A`/`B`/`0` values are realism violations; fix them rather than deleting examples.
3. Apply changes
   - Remove only the examples that match the agreed severity rule.
   - Update review CSV files in the examples root to remove deleted examples.
   - Replace placeholder `attachments_sha256` with realistic 64-hex values in remaining examples.
4. Verify
   - Ensure CSVs reference only existing example directories.
   - Confirm no placeholder hashes remain.

## Scripted Cleanup
Use `scripts/synthetic/prune_synthetics.py` for deterministic cleanup. Default mode is dry-run.

Examples:
```bash
python scripts/synthetic/prune_synthetics.py \
  --examples-dir tenants/<tenant_id>/datasets/synthetic_artifacts \
  --max-words 10
```
```bash
python scripts/synthetic/prune_synthetics.py \
  --examples-dir tenants/<tenant_id>/datasets/synthetic_artifacts \
  --max-words 10 \
  --apply
```

## Guardrails
- Do not modify tenant source artifacts under `tenants/*/source_artifacts/`.
- Keep changes scoped to synthetic example folders and their review CSVs.
- If requirements or thresholds change, update this skill and document in auto-memory notes if needed.
