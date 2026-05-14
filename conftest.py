# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

REQUIRES_LOCAL_DATASETS_MARK = "requires_local_datasets"


def _tenant_test_context(item: pytest.Item) -> tuple[str, Path] | None:
    path = Path(str(item.fspath))
    parts = list(path.parts)
    if "tenants" not in parts:
        return None
    idx = parts.index("tenants")
    if len(parts) <= idx + 2:
        return None
    tenant_id = parts[idx + 1]
    if parts[idx + 2] != "tests":
        return None
    repo_root = Path(__file__).resolve().parent
    dataset_dir = repo_root / "tenants" / tenant_id / "datasets"
    return tenant_id, dataset_dir


def _requires_local_datasets(item: pytest.Item) -> bool:
    return item.get_closest_marker(REQUIRES_LOCAL_DATASETS_MARK) is not None


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        f"{REQUIRES_LOCAL_DATASETS_MARK}: mark tests that need local tenant datasets (*.jsonl).",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        if not _requires_local_datasets(item):
            continue
        context = _tenant_test_context(item)
        if context is None:
            continue
        tenant_id, dataset_dir = context
        dataset_present = dataset_dir.exists() and any(dataset_dir.rglob("*.jsonl"))
        if not dataset_present:
            item.add_marker(
                pytest.mark.skip(
                    reason=(
                        f"Skipping dataset-dependent tests for `{tenant_id}` "
                        "because local datasets are missing."
                    )
                )
            )


def pytest_terminal_summary(terminalreporter: Any, exitstatus: int, config: pytest.Config) -> None:
    skipped = terminalreporter.stats.get("skipped", [])
    dataset_skips: dict[str, int] = {}
    for report in skipped:
        msg = report.longrepr[-1] if report.longrepr else ""
        if "because local datasets are missing" not in str(msg):
            continue
        # Extract tenant id from the skip reason
        reason = str(msg)
        start = reason.find("`")
        end = reason.find("`", start + 1)
        if start != -1 and end != -1:
            tenant_id = reason[start + 1 : end]
            dataset_skips[tenant_id] = dataset_skips.get(tenant_id, 0) + 1

    if not dataset_skips:
        return

    total = sum(dataset_skips.values())
    terminalreporter.section("Missing local datasets")
    terminalreporter.write_line(
        f"{total} test(s) skipped because local datasets are missing:"
    )
    for tenant_id, count in sorted(dataset_skips.items()):
        terminalreporter.write_line(f"  - {tenant_id}: {count} test(s)")
    terminalreporter.write_line("")
    terminalreporter.write_line(
        "To fetch datasets: python -m hephaestus.cli customer-data pull --tenant <tenant_id>"
    )
