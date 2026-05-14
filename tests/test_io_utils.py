# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from src.hephaestus.runs.io_utils import write_outputs


def test_write_outputs_normalizes_breakdown_by_total_cases(tmp_path: Path):
    output_dir = tmp_path / "out"
    run_config = {"tenant_id": "demo"}
    results = [
        {"case_id": "c1", "composite_score": 80.0, "score_breakdown": {"format": 100.0}},
        {"case_id": "c2", "composite_score": 0.0, "score_breakdown": {}},
    ]

    write_outputs(output_dir, run_config, results)

    summary = (output_dir / "summary.md").read_text(encoding="utf-8")
    assert "- format: 50.00" in summary
