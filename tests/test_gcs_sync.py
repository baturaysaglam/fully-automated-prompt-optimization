# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.hephaestus.storage.config import TenantStorageConfig
from src.hephaestus.storage.gcs_sync import (
    _parse_rsync_dry_run,
    pull_customer_data,
    push_customer_data,
    remove_local_customer_data,
)


def _config(tmp_path: Path) -> TenantStorageConfig:
    return TenantStorageConfig(
        tenant_id="demo",
        bucket="bucket-a",
        prefix="tenants/demo",
        raw_local=tmp_path / "tenants" / "demo" / "source_artifacts",
        derived_local=tmp_path / "tenants" / "demo" / "datasets",
        code_local=tmp_path / "tenants" / "demo" / "code",
    )


def test_pull_customer_data_builds_rsync_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = _config(tmp_path)
    calls = []

    def fake_run(args, check, capture_output, text):
        calls.append(args)
        return SimpleNamespace(stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    pull_customer_data(cfg, "all")
    assert calls[0][:5] == ["gsutil", "-m", "rsync", "-r", "gs://bucket-a/tenants/demo/raw/"]
    assert calls[1][:5] == ["gsutil", "-m", "rsync", "-r", "gs://bucket-a/tenants/demo/derived/"]


def test_push_uses_rsync(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = _config(tmp_path)
    cfg.raw_local.mkdir(parents=True, exist_ok=True)
    (cfg.raw_local / "a.txt").write_text("x", encoding="utf-8")

    calls = []

    def fake_run(args, check, capture_output, text):
        calls.append(args)
        return SimpleNamespace(stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    summaries = push_customer_data(cfg, "raw", force=True)

    assert calls[0] == [
        "gsutil", "-m", "rsync", "-r",
        str(cfg.raw_local),
        "gs://bucket-a/tenants/demo/raw/",
    ]
    assert summaries[0]["operation"] == "push"


def test_remove_local_requires_yes(tmp_path: Path):
    cfg = _config(tmp_path)
    with pytest.raises(ValueError, match="without --yes"):
        remove_local_customer_data(cfg, "raw", require_yes=False)


def test_parse_rsync_dry_run_forward():
    gcs_uri = "gs://bucket-a/tenants/demo/raw/"
    output = (
        "Building synchronization state...\n"
        "Starting synchronization...\n"
        "Would copy file://local/a.txt to gs://bucket-a/tenants/demo/raw/a.txt\n"
        "Would copy file://local/b.txt to gs://bucket-a/tenants/demo/raw/b.txt\n"
    )
    assert _parse_rsync_dry_run(output, gcs_uri) == {"a.txt", "b.txt"}


def test_parse_rsync_dry_run_reverse():
    gcs_uri = "gs://bucket-a/tenants/demo/raw/"
    output = (
        "Would copy gs://bucket-a/tenants/demo/raw/a.txt to file://local/a.txt\n"
        "Would copy gs://bucket-a/tenants/demo/raw/c.txt to file://local/c.txt\n"
    )
    assert _parse_rsync_dry_run(output, gcs_uri) == {"a.txt", "c.txt"}


def test_parse_rsync_dry_run_filename_containing_to():
    gcs_uri = "gs://bucket-a/tenants/demo/raw/"
    output = (
        "Would copy gs://bucket-a/tenants/demo/raw/intro to ml.txt"
        " to file://local/intro to ml.txt\n"
    )
    assert _parse_rsync_dry_run(output, gcs_uri) == {"intro to ml.txt"}


def test_push_blocks_when_clobber_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = _config(tmp_path)
    cfg.raw_local.mkdir(parents=True, exist_ok=True)
    (cfg.raw_local / "a.txt").write_text("x", encoding="utf-8")

    gcs_uri = "gs://bucket-a/tenants/demo/raw/"

    def fake_run(args, check, capture_output, text):
        if "-n" in args:
            # Both dry-runs report a.txt → intersection = clobber
            return SimpleNamespace(
                stdout=f"Would copy file://local/a.txt to {gcs_uri}a.txt\n",
                stderr="",
            )
        raise AssertionError("Real rsync should not be called when clobber detected")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(ValueError, match="would overwrite 1 existing GCS"):
        push_customer_data(cfg, "raw")


def test_push_proceeds_when_no_clobber(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = _config(tmp_path)
    cfg.raw_local.mkdir(parents=True, exist_ok=True)
    (cfg.raw_local / "a.txt").write_text("x", encoding="utf-8")

    gcs_uri = "gs://bucket-a/tenants/demo/raw/"
    calls = []

    def fake_run(args, check, capture_output, text):
        calls.append(args)
        if "-n" in args:
            if args[-1] == gcs_uri:
                # Forward: local file would be pushed
                return SimpleNamespace(
                    stdout=f"Would copy file://local/a.txt to {gcs_uri}a.txt\n",
                    stderr="",
                )
            else:
                # Reverse: nothing on GCS
                return SimpleNamespace(stdout="", stderr="")
        return SimpleNamespace(stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    summaries = push_customer_data(cfg, "raw")

    assert summaries[0]["operation"] == "push"
    # Verify the actual rsync was called (not just dry-runs)
    rsync_calls = [c for c in calls if "-n" not in c]
    assert len(rsync_calls) == 1


def test_push_force_allows_clobber(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = _config(tmp_path)
    cfg.raw_local.mkdir(parents=True, exist_ok=True)
    (cfg.raw_local / "a.txt").write_text("x", encoding="utf-8")

    calls = []

    def fake_run(args, check, capture_output, text):
        calls.append(args)
        return SimpleNamespace(stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    summaries = push_customer_data(cfg, "raw", force=True)

    assert summaries[0]["operation"] == "push"
    # With force=True, no dry-run calls should be made
    dry_run_calls = [c for c in calls if "-n" in c]
    assert len(dry_run_calls) == 0


def test_push_empty_gcs_prefix_succeeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = _config(tmp_path)
    cfg.raw_local.mkdir(parents=True, exist_ok=True)
    (cfg.raw_local / "a.txt").write_text("x", encoding="utf-8")

    gcs_uri = "gs://bucket-a/tenants/demo/raw/"
    calls = []

    def fake_run(args, check, capture_output, text):
        calls.append(args)
        if "-n" in args:
            if args[-1] == gcs_uri:
                # Forward: local files would be pushed
                return SimpleNamespace(
                    stdout=f"Would copy file://local/a.txt to {gcs_uri}a.txt\n",
                    stderr="",
                )
            else:
                # Reverse: GCS is empty, nothing to pull
                return SimpleNamespace(stdout="", stderr="")
        return SimpleNamespace(stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    summaries = push_customer_data(cfg, "raw")

    assert summaries[0]["operation"] == "push"


def test_push_all_preflights_before_uploading(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """When scope=all, clobber on the second scope must block the first from uploading."""
    cfg = _config(tmp_path)
    cfg.raw_local.mkdir(parents=True, exist_ok=True)
    (cfg.raw_local / "ok.txt").write_text("x", encoding="utf-8")
    cfg.derived_local.mkdir(parents=True, exist_ok=True)
    (cfg.derived_local / "conflict.txt").write_text("x", encoding="utf-8")

    raw_uri = "gs://bucket-a/tenants/demo/raw/"
    derived_uri = "gs://bucket-a/tenants/demo/derived/"

    def fake_run(args, check, capture_output, text):
        if "-n" in args:
            if args[-1] == raw_uri:
                # Forward dry-run for raw: new file, no clobber
                return SimpleNamespace(
                    stdout=f"Would copy file://ok.txt to {raw_uri}ok.txt\n",
                    stderr="",
                )
            if args[-2] == raw_uri:
                # Reverse dry-run for raw: nothing on GCS
                return SimpleNamespace(stdout="", stderr="")
            if args[-1] == derived_uri:
                # Forward dry-run for derived: would push conflict.txt
                return SimpleNamespace(
                    stdout=f"Would copy file://conflict.txt to {derived_uri}conflict.txt\n",
                    stderr="",
                )
            if args[-2] == derived_uri:
                # Reverse dry-run for derived: conflict.txt exists on GCS
                return SimpleNamespace(
                    stdout=f"Would copy {derived_uri}conflict.txt to file://conflict.txt\n",
                    stderr="",
                )
        raise AssertionError("No upload should happen when clobber is detected")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(ValueError, match="would overwrite 1 existing GCS"):
        push_customer_data(cfg, "all")


def test_remove_local_recreates_gitkeep(tmp_path: Path):
    cfg = _config(tmp_path)
    cfg.derived_local.mkdir(parents=True, exist_ok=True)
    (cfg.derived_local / "README.md").write_text("# datasets\n", encoding="utf-8")
    (cfg.derived_local / "x.jsonl").write_text("{}", encoding="utf-8")
    (cfg.derived_local / "nested").mkdir()
    (cfg.derived_local / "nested" / "artifact.txt").write_text("artifact", encoding="utf-8")

    remove_local_customer_data(cfg, "derived", require_yes=True)
    assert (cfg.derived_local / ".gitkeep").exists()
    assert (cfg.derived_local / "README.md").exists()
    assert not (cfg.derived_local / "x.jsonl").exists()
    assert not (cfg.derived_local / "nested").exists()
