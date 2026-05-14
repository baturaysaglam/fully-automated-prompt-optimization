# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

SCRIPT_PATH = Path("scripts/synthetic/prune_synthetics.py")


def _load_pruner_module():
    spec = importlib.util.spec_from_file_location("prune_synthetics", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_update_csv_preserves_schema_and_uses_example_id(tmp_path: Path):
    module = _load_pruner_module()
    csv_path = tmp_path / "labels_review.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["example_id", "proposed_label", "indicators", "notes"])
        writer.writeheader()
        writer.writerow(
            {
                "example_id": "keep-me",
                "proposed_label": "malicious",
                "indicators": "x",
                "notes": "preserve",
            }
        )
        writer.writerow(
            {
                "example_id": "delete-me",
                "proposed_label": "non-malicious",
                "indicators": "y",
                "notes": "remove",
            }
        )

    module.update_csv(csv_path, {"delete-me"}, apply=True)

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == ["example_id", "proposed_label", "indicators", "notes"]
    assert rows == [
        {
            "example_id": "keep-me",
            "proposed_label": "malicious",
            "indicators": "x",
            "notes": "preserve",
        }
    ]
