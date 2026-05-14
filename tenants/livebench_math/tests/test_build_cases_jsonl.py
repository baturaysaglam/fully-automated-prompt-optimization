# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the LiveBench Math dataset builder."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tenants.livebench_math.code.build_cases_jsonl import _convert_case, build_all


def _make_hf_row(idx: int = 0, task: str = "math_competitions", subtask: str = "amc_2024") -> dict:
    """Create a fake HuggingFace LiveBench Math row."""
    return {
        "question_id": f"lb_math_{idx:04d}",
        "task": task,
        "subtask": subtask,
        "category": "math",
        "turns": [f"What is the answer to problem {idx}?"],
        "ground_truth": "C",
    }


class TestConvertCase:
    def test_basic_conversion(self) -> None:
        row = _make_hf_row(0)
        case = _convert_case(row, 0)

        assert case["case_id"] == "lb_math_0000"
        assert case["task_type"] == "math"
        assert case["context"]["question"] == "What is the answer to problem 0?"
        assert case["expected"]["question_d"] == row
        assert case["metadata"]["source"] == "livebench/math"
        assert case["metadata"]["task"] == "math_competitions"
        assert case["metadata"]["subtask"] == "amc_2024"

    def test_uses_question_id_from_row(self) -> None:
        row = _make_hf_row(5)
        row["question_id"] = "custom_id_123"
        case = _convert_case(row, 5)
        assert case["case_id"] == "custom_id_123"

    def test_fallback_case_id_when_no_question_id(self) -> None:
        row = _make_hf_row(7)
        del row["question_id"]
        case = _convert_case(row, 7)
        assert case["case_id"] == "livebench_math_0007"


class TestBuildAll:
    @patch("tenants.livebench_math.code.build_cases_jsonl.load_dataset")
    def test_splits_correct_sizes(self, mock_load_dataset, tmp_path) -> None:
        """build_all should produce correct split sizes (33/33/34%)."""
        rows = [_make_hf_row(i) for i in range(100)]
        mock_load_dataset.return_value = rows

        with patch("tenants.livebench_math.code.build_cases_jsonl.OUTPUT_DIR", tmp_path):
            counts = build_all()

        assert counts["train"] == 33
        assert counts["val"] == 33
        assert counts["test"] == 34

    @patch("tenants.livebench_math.code.build_cases_jsonl.load_dataset")
    def test_deterministic_with_seed(self, mock_load_dataset, tmp_path) -> None:
        """Same data should produce same splits (seed=0)."""
        rows = [_make_hf_row(i) for i in range(50)]
        mock_load_dataset.return_value = rows

        for run_dir in (tmp_path / "a", tmp_path / "b"):
            with patch("tenants.livebench_math.code.build_cases_jsonl.OUTPUT_DIR", run_dir):
                build_all()

        for split in ("train.jsonl", "val.jsonl", "test.jsonl"):
            a_content = (tmp_path / "a" / split).read_text()
            b_content = (tmp_path / "b" / split).read_text()
            assert a_content == b_content
