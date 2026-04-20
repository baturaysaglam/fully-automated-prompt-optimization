<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Eval Config Schema

Evaluation configs use the **LangGraph chain** format. The chain is a compiled `StateGraph` built by a factory function in a tenant-defined Python module.

```json
{
  "tenant_id": "<tenant_id>",
  "provider": "<baseten|base10|sagemaker|openai>",
  "provider_settings": { "...": "..." },
  "dataset": {"path": "tenants/<tenant_id>/datasets/datasets/cases.jsonl"},
  "chain": {
    "path": "tenants/<tenant_id>/chains/<chain_module>.py",
    "fn": "build_chain",
    "config": {
      "prompt_paths": {
        "<step_name>": "tenants/<tenant_id>/prompts/variants/<variant>.md"
      }
    }
  },
  "scoring_profile": { "...": "..." },
  "output_dir": "tenants/<tenant_id>/evals/tmp/<run-name>"
}
```

### `chain` fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | yes | — | Path to the chain Python module (`.py` file) containing the factory function |
| `fn` | string | no | `"build_chain"` | Name of the factory function to call |
| `config` | object | no | `{}` | Arbitrary config dict passed to the factory function (e.g., prompt paths, parameters) |

The factory function signature must be:

```python
def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> CompiledGraph
```

### Validation rules

- `chain` is required — configs without it raise `ValueError`
- `chain.path` must be non-empty

## Provider Settings

`provider_settings` depends on the provider:

- `baseten` / `base10`: `base_url`, `model`, plus shared sampling/retry settings above.
- `sagemaker`: `api_url`, `api_key_env` (default `X_API_KEY`), plus shared sampling/retry settings above.
- `openai`: `model` (default `gpt-4o`), plus shared sampling/retry settings (`timeout_seconds`, `max_retries`, `retry_backoff_seconds`, `temperature`, `top_p`, `max_tokens`). Requires `OPENAI_API_KEY` environment variable.

## General Notes

Eval configs are ephemeral local files (for example, under
`tenants/<tenant_id>/configs/local-<run-name>.json`) and should not be committed.
A tracked starter template is available at
`docs/templates/eval-config.template.json`.

Storage operations use a separate tenant config at
`tenants/<tenant_id>/storage/config.json`, consumed by:

- `python -m hephaestus.cli customer-data pull ...`
- `python -m hephaestus.cli customer-data push ...` (use `--force` to overwrite existing GCS objects)
- `python -m hephaestus.cli customer-data remove-local --yes ...`

Notes:
- Core only requires `scoring_profile.scorer.module_path` (and optionally `class_name`).
- Other fields in `scoring_profile` are tenant-defined and interpreted by the tenant scorer.
