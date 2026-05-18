<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Operations

## Config Matrix
| Config | Model | Split | Purpose |
|--------|-------|-------|---------|
| `local-gpt41mini-val-variant001.json` | GPT-4.1-mini | val | Optimization |
| `local-gpt41mini-test-variant001.json` | GPT-4.1-mini | test | Final eval |
| `local-deepseek-test-variant001.json` | DeepSeek-V3.1 | test | Final eval |

## Standard Eval Commands
- Preferred: `/project:eval-runner` with the appropriate config
- K8s (always remote): `NAMESPACE=your-namespace bash deploy/scripts/run_eval.sh --config tenants/aime2025/configs/<config>.json --detach`

## Success Criteria
Baseline CoT scores should be in the neighborhood of the ETGPO paper:
- GPT-4.1-mini: ~47% accuracy
- DeepSeek-V3.1: ~65% accuracy

After optimization, target:
- GPT-4.1-mini: >= 60%
- DeepSeek-V3.1: >= 64%

## Failure Triage
- Check `evals/tmp/<run>/summary.md` for aggregate scores.
- Check `evals/tmp/<run>/results.jsonl` for per-case breakdown.
- If scores are significantly below baseline, check answer extraction (some models may not use `\boxed{}` format).
- Temperature=1.0 means high variance per run; use multiple runs for reliable scores.

## Output Management
- `evals/tmp/` — transient eval outputs, not committed.
- `evals/archive/` — milestone snapshots, not committed.
- Eval outputs are local-only; results are summarized in `docs/change-log.md`.
