<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Config Matrix
| Config | Prompt Variant | Dataset | Model |
|--------|---------------|---------|-------|
| `local-classify-variant001.json` | `variant-001.md` | `test.jsonl` | gpt-4.1-mini |

## Standard Eval Commands
- Preferred: `/project:eval-runner` with config `tenants/cti_rcm/configs/local-classify-variant001.json`
- Direct: `python -m hephaestus.cli eval --config tenants/cti_rcm/configs/local-classify-variant001.json`

## K8s Eval (K8s cluster)

See [deploy/README.md](../../../deploy/README.md) for cluster setup and full docs.

```bash
deploy/scripts/run_eval.sh --config tenants/cti_rcm/configs/<config>.json --detach
```

Each run creates a dedicated pod named `hephaestus-cti_rcm-<hash>` with isolated workspace and results. Config files are gitignored — use your local config.

## Success Criteria
- Baseline establishment: record initial accuracy on 1000-case test set.
- Target: improve beyond faith's published baseline through prompt iteration.

## Failure Triage
- Check `evals/tmp/classify-variant001/summary.md` for aggregate scores.
- Check `evals/tmp/classify-variant001/results.jsonl` for per-case breakdown.
- `answer_format: "invalid"` indicates the model failed to output a parseable CWE ID.

## Output Management
- `evals/tmp/` — transient eval outputs, not committed.
- `evals/archive/` — milestone snapshots, not committed.
- Eval outputs are local-only; results are summarized in `docs/change-log.md`.
