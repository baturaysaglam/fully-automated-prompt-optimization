# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the IFBench dataset builder."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tenants.ifbench.code.build_cases_jsonl import _convert_case, build_all


def _make_row(idx: int = 0) -> dict:
    """Create a fake IFBench row."""
    return {
        "prompt": f"Write a response that satisfies constraint {idx}.",
        "instruction_id_list": ["count:word_count_range"],
        "kwargs": [{"min_words": 10, "max_words": 100}],
    }


class TestConvertCase:
    def test_basic_conversion(self) -> None:
        row = _make_row(0)
        case = _convert_case(row, 0, "train")

        assert case["case_id"] == "ifbench_train_0000"
        assert case["task_type"] == "instruction_following"
        assert case["context"]["prompt"] == row["prompt"]
        assert case["expected"]["instruction_id_list"] == row["instruction_id_list"]
        assert case["expected"]["kwargs"] == row["kwargs"]
        assert case["metadata"]["source"] == "IFBench_train"


class TestBuildAll:
    def test_correct_split_sizes(self, tmp_path: Path) -> None:
        """build_all should produce 300 val, 150 train, 294 test."""
        # Write fake source artifacts
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        train_file = source_dir / "IFBench_train.jsonl"
        with open(train_file, "w") as f:
            for i in range(500):
                f.write(json.dumps(_make_row(i)) + "\n")

        test_file = source_dir / "IFBench_test.jsonl"
        with open(test_file, "w") as f:
            for i in range(294):
                f.write(json.dumps(_make_row(i)) + "\n")

        output_dir = tmp_path / "output"

        with patch("tenants.ifbench.code.build_cases_jsonl.SOURCE_DIR", source_dir):
            with patch("tenants.ifbench.code.build_cases_jsonl.OUTPUT_DIR", output_dir):
                counts = build_all()

        assert counts["val"] == 300
        assert counts["train"] == 150
        assert counts["test"] == 294

    def test_output_files_valid_jsonl(self, tmp_path: Path) -> None:
        """All output lines should be valid JSON."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        with open(source_dir / "IFBench_train.jsonl", "w") as f:
            for i in range(500):
                f.write(json.dumps(_make_row(i)) + "\n")

        with open(source_dir / "IFBench_test.jsonl", "w") as f:
            for i in range(10):
                f.write(json.dumps(_make_row(i)) + "\n")

        output_dir = tmp_path / "output"

        with patch("tenants.ifbench.code.build_cases_jsonl.SOURCE_DIR", source_dir):
            with patch("tenants.ifbench.code.build_cases_jsonl.OUTPUT_DIR", output_dir):
                build_all()

        for fname in ("train.jsonl", "val.jsonl", "test.jsonl"):
            with open(output_dir / fname) as f:
                for line in f:
                    case = json.loads(line)
                    assert "case_id" in case
                    assert "context" in case
                    assert "expected" in case
