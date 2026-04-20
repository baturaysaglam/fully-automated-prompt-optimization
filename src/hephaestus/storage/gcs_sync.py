# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from .config import TenantStorageConfig


@dataclass(frozen=True)
class StorageTarget:
    scope: str
    local_path: Path
    gcs_uri: str


def _scopes(scope: str) -> List[str]:
    normalized = scope.strip().lower()
    if normalized == "all":
        return ["raw", "derived"]
    if normalized in {"raw", "derived"}:
        return [normalized]
    raise ValueError("Scope must be one of: raw, derived, all.")


def _build_targets(config: TenantStorageConfig, scope: str) -> List[StorageTarget]:
    targets: List[StorageTarget] = []
    for item in _scopes(scope):
        local_path = config.raw_local if item == "raw" else config.derived_local
        gcs_uri = f"gs://{config.bucket}/{config.prefix}/{item}/"
        targets.append(StorageTarget(scope=item, local_path=local_path, gcs_uri=gcs_uri))
    return targets


def _run_gsutil(args: List[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("`gsutil` is required but was not found in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(f"gsutil command failed: {' '.join(args)}\n{details}") from exc


def _parse_rsync_dry_run(output: str, gcs_uri: str) -> Set[str]:
    """Extract GCS-relative paths from rsync -n output.

    Dry-run lines look like:
        Would copy file://local/a to gs://bucket/prefix/a
    or  Would copy gs://bucket/prefix/a to file://local/a
    We extract the path relative to gcs_uri from whichever side matches.
    """
    keys: Set[str] = set()
    for line in output.splitlines():
        if not line.startswith("Would copy "):
            continue
        idx = line.find(gcs_uri)
        if idx == -1:
            continue
        rel = line[idx + len(gcs_uri) :]
        # In reverse lines the GCS path is followed by " to file://...";
        # split on " to file://" rather than " to " to handle object names
        # that contain " to " (e.g. "intro to ml.txt").
        rel = rel.split(" to file://")[0].strip()
        if rel:
            keys.add(rel)
    return keys


def _detect_clobber(local_path: Path, gcs_uri: str) -> List[str]:
    """Return list of GCS-relative paths that would be overwritten."""
    fwd = _run_gsutil(["gsutil", "-m", "rsync", "-n", "-r", str(local_path), gcs_uri])
    rev = _run_gsutil(["gsutil", "-m", "rsync", "-n", "-r", gcs_uri, str(local_path)])
    fwd_keys = _parse_rsync_dry_run(fwd.stdout + "\n" + fwd.stderr, gcs_uri)
    rev_keys = _parse_rsync_dry_run(rev.stdout + "\n" + rev.stderr, gcs_uri)
    return sorted(fwd_keys & rev_keys)


def pull_customer_data(config: TenantStorageConfig, scope: str) -> List[Dict[str, str]]:
    summaries: List[Dict[str, str]] = []
    for target in _build_targets(config, scope):
        target.local_path.mkdir(parents=True, exist_ok=True)
        cmd = ["gsutil", "-m", "rsync", "-r", target.gcs_uri, str(target.local_path)]
        _run_gsutil(cmd)
        summaries.append(
            {
                "scope": target.scope,
                "local_path": str(target.local_path),
                "gcs_uri": target.gcs_uri,
                "operation": "pull",
            }
        )
    return summaries


def push_customer_data(
    config: TenantStorageConfig, scope: str, *, force: bool = False
) -> List[Dict[str, str]]:
    """Push local customer data to GCS via rsync.

    When *force* is False, a preflight dry-run detects files that would be
    overwritten and raises ValueError listing them.  There is a small TOCTOU
    window between the check and the actual upload; this is acceptable because
    customer-data push is a manual single-operator CLI command.
    """
    targets = _build_targets(config, scope)

    # Preflight: check all scopes for clobber before uploading any, so that
    # a conflict in a later scope doesn't leave an earlier scope already pushed.
    if not force:
        all_clobbered: List[str] = []
        for target in targets:
            if not target.local_path.exists():
                continue
            clobbered = _detect_clobber(target.local_path, target.gcs_uri)
            all_clobbered.extend(
                f"{target.gcs_uri}{f}" for f in clobbered
            )
        if all_clobbered:
            raise ValueError(
                f"Push would overwrite {len(all_clobbered)} existing GCS object(s):\n"
                + "\n".join(f"  {f}" for f in all_clobbered)
                + "\nUse --force to overwrite."
            )

    summaries: List[Dict[str, str]] = []
    for target in targets:
        if not target.local_path.exists():
            summaries.append(
                {
                    "scope": target.scope,
                    "local_path": str(target.local_path),
                    "gcs_uri": target.gcs_uri,
                    "operation": "push",
                }
            )
            continue

        cmd = ["gsutil", "-m", "rsync", "-r", str(target.local_path), target.gcs_uri]
        _run_gsutil(cmd)
        summaries.append(
            {
                "scope": target.scope,
                "local_path": str(target.local_path),
                "gcs_uri": target.gcs_uri,
                "operation": "push",
            }
        )
    return summaries


def remove_local_customer_data(
    config: TenantStorageConfig, scope: str, require_yes: bool
) -> List[Dict[str, str]]:
    if not require_yes:
        raise ValueError("Refusing to remove local customer data without --yes.")

    preserved_names = {"README.md", ".gitkeep"}
    summaries: List[Dict[str, str]] = []
    for target in _build_targets(config, scope):
        target.local_path.mkdir(parents=True, exist_ok=True)
        for child in target.local_path.iterdir():
            if child.name in preserved_names:
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        (target.local_path / ".gitkeep").write_text("", encoding="utf-8")
        summaries.append(
            {
                "scope": target.scope,
                "local_path": str(target.local_path),
                "operation": "remove_local",
            }
        )
    return summaries
