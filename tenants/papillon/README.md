<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Papillon Tenant

Privacy-preserving prompting benchmark. Evaluates PII redaction quality and
response reconstruction from an untrusted LLM.

## Quick Start

```bash
# Build datasets from HuggingFace
python tenants/papillon/code/build_cases_jsonl.py

# Run evaluation
python -m hephaestus.cli eval --config tenants/papillon/configs/local-chain-variant001.json

# Run tests
python -m pytest tenants/papillon/tests/ -v
```

## Dependencies

No extra dependencies beyond core (uses OpenAI API for untrusted calls and judging).
