# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import conftest


class _FakeItem:
    def __init__(self, path: Path, requires_local_datasets: bool):
        self.fspath = str(path)
        self._requires_local_datasets = requires_local_datasets
        self.markers = []

    def get_closest_marker(self, name: str):
        if self._requires_local_datasets and name == conftest.REQUIRES_LOCAL_DATASETS_MARK:
            return object()
        return None

    def add_marker(self, marker):
        self.markers.append(marker)


def test_collection_hook_skips_only_dataset_marked_tenant_tests():
    needs_dataset = _FakeItem(
        Path("tenants/demo/tests/test_dataset_contract.py"),
        requires_local_datasets=True,
    )
    does_not_need_dataset = _FakeItem(
        Path("tenants/demo/tests/test_legacy_migration.py"),
        requires_local_datasets=False,
    )

    conftest.pytest_collection_modifyitems(  # type: ignore[arg-type]
        config=None, items=[needs_dataset, does_not_need_dataset]
    )

    assert len(needs_dataset.markers) == 1
    assert len(does_not_need_dataset.markers) == 0


def test_collection_hook_does_not_skip_non_tenant_tests():
    non_tenant = _FakeItem(
        Path("tests/test_something.py"),
        requires_local_datasets=True,
    )

    conftest.pytest_collection_modifyitems(config=None, items=[non_tenant])  # type: ignore[arg-type]

    assert len(non_tenant.markers) == 0
