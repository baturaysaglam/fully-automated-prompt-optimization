# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

import pytest

from src.hephaestus.storage.config import DEFAULT_BUCKET, load_storage_config


def test_load_storage_config_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    tenant_dir = tmp_path / "tenants" / "demo"
    (tenant_dir / "storage").mkdir(parents=True)
    config_path = tenant_dir / "storage" / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "tenant_id": "demo",
                "gcs": {"bucket": "bucket-a", "prefix": "tenants/demo"},
                "paths": {
                    "raw_local": "tenants/demo/source_artifacts",
                    "derived_local": "tenants/demo/datasets",
                    "code_local": "tenants/demo/code",
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_storage_config("demo", config_path)
    assert config.tenant_id == "demo"
    assert config.bucket == "bucket-a"
    assert config.prefix == "tenants/demo"


def test_load_storage_config_uses_default_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    tenant_dir = tmp_path / "tenants" / "demo"
    (tenant_dir / "storage").mkdir(parents=True)
    (tenant_dir / "storage" / "config.json").write_text(
        json.dumps(
            {
                "tenant_id": "demo",
                "gcs": {"bucket": "bucket-a", "prefix": "tenants/demo"},
                "paths": {
                    "raw_local": "tenants/demo/source_artifacts",
                    "derived_local": "tenants/demo/datasets",
                    "code_local": "tenants/demo/code",
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_storage_config("demo")
    assert config.tenant_id == "demo"


def test_load_storage_config_rejects_mismatched_tenant(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "storage.json"
    config_path.write_text(
        json.dumps(
            {
                "tenant_id": "wrong",
                "gcs": {"bucket": "bucket-a", "prefix": "tenants/wrong"},
                "paths": {
                    "raw_local": "tenants/demo/source_artifacts",
                    "derived_local": "tenants/demo/datasets",
                    "code_local": "tenants/demo/code",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not match"):
        load_storage_config("demo", config_path)


def test_load_storage_config_rejects_paths_outside_tenant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "storage.json"
    config_path.write_text(
        json.dumps(
            {
                "tenant_id": "demo",
                "gcs": {"bucket": "bucket-a", "prefix": "tenants/demo"},
                "paths": {
                    "raw_local": "/tmp/not-tenant",
                    "derived_local": "tenants/demo/datasets",
                    "code_local": "tenants/demo/code",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must live under"):
        load_storage_config("demo", config_path)


def test_load_storage_config_rejects_tenant_root_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "storage.json"
    config_path.write_text(
        json.dumps(
            {
                "tenant_id": "demo",
                "gcs": {"bucket": "bucket-a", "prefix": "tenants/demo"},
                "paths": {
                    "raw_local": "tenants/demo",
                    "derived_local": "tenants/demo/datasets",
                    "code_local": "tenants/demo/code",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="strict subdirectory"):
        load_storage_config("demo", config_path)


def test_default_bucket_constant():
    assert DEFAULT_BUCKET == "your-gcs-bucket-name"


def test_load_storage_config_falls_back_to_default_bucket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    tenant_dir = tmp_path / "tenants" / "demo"
    (tenant_dir / "storage").mkdir(parents=True)
    config_path = tenant_dir / "storage" / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "tenant_id": "demo",
                "gcs": {"prefix": "tenants/demo"},
                "paths": {
                    "raw_local": "tenants/demo/source_artifacts",
                    "derived_local": "tenants/demo/datasets",
                    "code_local": "tenants/demo/code",
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_storage_config("demo", config_path)
    assert config.bucket == DEFAULT_BUCKET


def test_load_storage_config_explicit_bucket_overrides_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    tenant_dir = tmp_path / "tenants" / "demo"
    (tenant_dir / "storage").mkdir(parents=True)
    config_path = tenant_dir / "storage" / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "tenant_id": "demo",
                "gcs": {"bucket": "custom-bucket", "prefix": "tenants/demo"},
                "paths": {
                    "raw_local": "tenants/demo/source_artifacts",
                    "derived_local": "tenants/demo/datasets",
                    "code_local": "tenants/demo/code",
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_storage_config("demo", config_path)
    assert config.bucket == "custom-bucket"


def test_load_storage_config_rejects_empty_bucket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    tenant_dir = tmp_path / "tenants" / "demo"
    (tenant_dir / "storage").mkdir(parents=True)
    config_path = tenant_dir / "storage" / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "tenant_id": "demo",
                "gcs": {"bucket": "", "prefix": "tenants/demo"},
                "paths": {
                    "raw_local": "tenants/demo/source_artifacts",
                    "derived_local": "tenants/demo/datasets",
                    "code_local": "tenants/demo/code",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="gcs.bucket"):
        load_storage_config("demo", config_path)


def test_load_storage_config_rejects_null_bucket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    tenant_dir = tmp_path / "tenants" / "demo"
    (tenant_dir / "storage").mkdir(parents=True)
    config_path = tenant_dir / "storage" / "config.json"
    config_path.write_text(
        '{"tenant_id":"demo","gcs":{"bucket":null,"prefix":"tenants/demo"},'
        '"paths":{"raw_local":"tenants/demo/source_artifacts",'
        '"derived_local":"tenants/demo/datasets","code_local":"tenants/demo/code"}}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="gcs.bucket"):
        load_storage_config("demo", config_path)
