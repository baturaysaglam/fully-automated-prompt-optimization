<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Output Paths

- Output path is controlled by `output_dir` in your local eval config (for example, `tenants/<tenant_id>/configs/local-<run-name>.json`).
- Typical working runs use `tenants/<tenant_id>/evals/tmp/<run-name>/`.
- Typical archived runs use `tenants/<tenant_id>/evals/archive/<run-name>/`.

## Files Written Per Run

- `summary.md`: Human-readable summary with check pass counts
- `results.jsonl`: One JSON object per example
- `run_config.json`: Parameters used for the run
