<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

---
description: >
  Run tenant evaluations and return score summaries.
  TRIGGER when: user wants to run an eval, test a prompt variant, check eval scores, execute an eval config, compare variant performance, or see evaluation results.
  DO NOT TRIGGER when: user is analyzing existing results (use optimization agent), creating synthetic data (use synthetic-samples), or editing prompts directly.
---

# Eval Runner

## Overview

Run a tenant evaluation config and return a concise summary plus the output directory path.

## Quick Start

1. Ensure provider credentials are available (for Baseten, `BASETEN_API_KEY`).
2. Create a local eval config from the tracked template (configs are ephemeral and ignored):

```bash
mkdir -p tenants/<tenant_id>/configs
cp docs/templates/eval-config.template.json tenants/<tenant_id>/configs/local-<run-name>.json
```

3. Run the helper script:

```bash
python scripts/eval/run_eval_and_summarize.py \
  --config tenants/<tenant_id>/configs/local-<run-name>.json
```

This runs `python -m hephaestus.cli eval --config ...` and prints the evaluation summary plus the output directory.

## Common Variations

- Run directly via CLI:

```bash
python -m hephaestus.cli eval --config tenants/<tenant_id>/configs/local-<run-name>.json
```

- Override output directory without editing your local config:

```bash
python scripts/eval/run_eval_and_summarize.py \
  --config tenants/<tenant_id>/configs/local-<run-name>.json \
  --output-dir tenants/<tenant_id>/evals/tmp/<run-name>
```

- Switch config for another prompt variant or dataset:

```bash
python scripts/eval/run_eval_and_summarize.py \
  --config tenants/<tenant_id>/configs/local-<other-run>.json
```

## Notes

- Output locations come from `output_dir` in config (or `--output-dir` override) and include `summary.md`, `results.jsonl`, and `run_config.json`.
- Eval configs should remain local-only in `tenants/<tenant_id>/configs/` and are not committed.
- `hephaestus.cli eval --dry-run` is intentionally disabled in this repo.

## Resources

### scripts/
- `scripts/eval/run_eval_and_summarize.py`: Runs the evaluation and prints a summary plus output directory.

### references/
- `docs/references/eval_paths.md`: Output locations and files.
