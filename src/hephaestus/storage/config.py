# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BUCKET: str = "your-gcs-bucket-name"


@dataclass(frozen=True)
class TenantStorageConfig:
    tenant_id: str
    bucket: str
    prefix: str
    raw_local: Path
    derived_local: Path
    code_local: Path


def _ensure_within_tenant(path: Path, tenant_root: Path, field: str) -> Path:
    resolved_path = path.resolve()
    resolved_root = tenant_root.resolve()
    if resolved_path == resolved_root:
        raise ValueError(
            f"Storage path `{field}` must be a strict subdirectory of `{tenant_root}`, not the tenant root."
        )
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        raise ValueError(f"Storage path `{field}` must live under `{tenant_root}`.")
    return resolved_path


def _read_required_str(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Storage config missing `{context}.{key}`.")
    return value.strip()


def load_storage_config(tenant_id: str, path: Path | None = None) -> TenantStorageConfig:
    storage_path = path or Path(f"tenants/{tenant_id}/storage/config.json")
    raw = json.loads(storage_path.read_text(encoding="utf-8"))

    config_tenant_id = _read_required_str(raw, "tenant_id", "root")
    if config_tenant_id != tenant_id:
        raise ValueError(
            f"Storage config tenant_id `{config_tenant_id}` does not match requested tenant `{tenant_id}`."
        )

    gcs = raw.get("gcs")
    if not isinstance(gcs, dict):
        raise ValueError("Storage config missing `gcs` object.")
    if "bucket" not in gcs:
        bucket = DEFAULT_BUCKET
    elif isinstance(gcs["bucket"], str) and gcs["bucket"].strip():
        bucket = gcs["bucket"].strip()
    else:
        raise ValueError(
            f"Storage config `gcs.bucket` must be a non-empty string (got {gcs['bucket']!r}). "
            "Remove the key entirely to use the default bucket."
        )
    prefix = _read_required_str(gcs, "prefix", "gcs").strip("/")

    paths = raw.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("Storage config missing `paths` object.")

    tenant_root = Path(f"tenants/{tenant_id}")
    raw_local = _ensure_within_tenant(
        Path(_read_required_str(paths, "raw_local", "paths")),
        tenant_root,
        "paths.raw_local",
    )
    derived_local = _ensure_within_tenant(
        Path(_read_required_str(paths, "derived_local", "paths")),
        tenant_root,
        "paths.derived_local",
    )
    code_local = _ensure_within_tenant(
        Path(_read_required_str(paths, "code_local", "paths")),
        tenant_root,
        "paths.code_local",
    )

    return TenantStorageConfig(
        tenant_id=tenant_id,
        bucket=bucket,
        prefix=prefix,
        raw_local=raw_local,
        derived_local=derived_local,
        code_local=code_local,
    )
