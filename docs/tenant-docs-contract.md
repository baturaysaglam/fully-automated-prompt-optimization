<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Documentation Contract

Every tenant under `tenants/<tenant_id>/` must include a minimum set of tenant-specific docs so skills and operators can run and iterate evals without guessing.

## Required Files

- `tenants/<tenant_id>/README.md`
- `tenants/<tenant_id>/docs/tenant-profile.md`
- `tenants/<tenant_id>/docs/data-contract.md`
- `tenants/<tenant_id>/docs/prompt-contract.md`
- `tenants/<tenant_id>/docs/eval-operations.md`
- `tenants/<tenant_id>/docs/iteration-playbook.md`
- `tenants/<tenant_id>/docs/change-log.md`
- `tenants/<tenant_id>/docs/docs-index.yaml`

## Canonical Lookup

Skills should resolve tenant docs from `docs/docs-index.yaml` first. If unavailable, they may fall back to default filenames.
Only files under `tenants/<tenant_id>/docs/` are canonical for tenant policy and operations.

## Non-Canonical Tenant Notes

`tenants/<tenant_id>/reports/` is reserved for local-only, point-in-time analysis notes that may drift.
Those reports are non-authoritative and must not be used as source-of-truth inputs for automation or policy decisions.

## Validation

Run:

```bash
python scripts/check_tenant_docs.py
```

To validate a specific tenant:

```bash
python scripts/check_tenant_docs.py --tenant <tenant_id>
```
