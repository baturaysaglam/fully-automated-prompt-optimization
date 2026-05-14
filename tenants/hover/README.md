<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# HoVer Tenant

3-hop claim verification via BM25 retrieval over Wikipedia abstracts. Evaluates
retrieval recall — whether all supporting documents are retrieved.

## Quick Start

```bash
# Build datasets from HuggingFace
python tenants/hover/code/build_cases_jsonl.py

# Run evaluation (BM25 index auto-builds on first run)
python -m hephaestus.cli eval --config tenants/hover/configs/local-chain-variant001.json

# Run tests
python -m pytest tenants/hover/tests/ -v
```

## Dependencies

```bash
pip install -e ".[hover]"
```

Requires: `bm25s`, `PyStemmer`, `ujson`, `diskcache`
