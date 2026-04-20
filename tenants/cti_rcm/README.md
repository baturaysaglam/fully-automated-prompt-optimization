<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# cti_rcm

## Purpose
CTI-CWE (Root Cause Mapping) evaluates an LLM's ability to map CVE descriptions to CWE IDs.
Based on the CTIBench benchmark (`AI4Sec/cti-bench`, subset `cti-rcm`).

## Status
- Lifecycle: active
- Last validated: 2026-03-17
- Owner: <your-name>

## Quick Links
- Tenant profile: `docs/tenant-profile.md`
- Data contract: `docs/data-contract.md`
- Prompt contract: `docs/prompt-contract.md`
- Eval operations: `docs/eval-operations.md`
- Iteration playbook: `docs/iteration-playbook.md`
- Change log: `docs/change-log.md`

Reference canonical global process guidance from tenant docs instead of duplicating it.

## Dependencies
Requires `cisco-foundation-ai-test-harness` (faith) for data loading and answer extraction:
```
pip install -e ".[cti_rcm]"
```

## Quick Run
```bash
# Build dataset
python tenants/cti_rcm/code/build_cases_jsonl.py

# Run eval
python -m hephaestus.cli eval --config tenants/cti_rcm/configs/local-classify-variant001.json
```

## Data Safety
- Do not modify `source_artifacts/` unless explicitly requested.
- Keep secrets out of committed files.
