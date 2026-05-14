<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Recommended Eval Settings

Single source of truth for hotpotqa eval configuration values.
Use these when creating new config files.

## GEPA-critical settings

These must match for valid comparisons against GEPA paper baselines.

| Setting | Value | Notes |
|---|---|---|
| `model` | `gpt-4.1-mini` | GEPA paper model |
| `temperature` | `1.0` | GEPA default |
| `retrieval_k` | `7` | Retrieval depth per hop |
| Scoring | pure EM (`composite_score` = `exact_match`) | No F1 blending |
| Chain | 6-node GEPA-aligned (`tenants/hotpotqa/chains/multi_hop.py`) | `build_chain` entry point |

## Frozen Parameters

The values in the GEPA-critical settings table above are **immutable during prompt optimization**.
The optimization agent must not modify `retrieval_k`, `temperature`, `top_p`, `model`, or any other
retrieval/model parameter. Changes to these values require explicit user approval outside the
automated optimization loop.

## Operational defaults

Not GEPA-specific but standardized across hotpotqa configs.

| Setting | Value |
|---|---|
| `max_workers` | `10` |
| `top_p` | `0.95` |
| `max_tokens` | `16000` |
| `timeout_seconds` | `300` |
| `max_retries` | `2` |
| `retry_backoff_seconds` | `5` |
| `bm25_data_dir` | `tenants/hotpotqa/data/bm25` |
