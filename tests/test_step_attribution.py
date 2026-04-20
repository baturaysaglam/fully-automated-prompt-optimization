# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for step_attribution module."""

from __future__ import annotations

import json
from pathlib import Path

from src.hephaestus.analysis.step_attribution import attribute_failures


class TestAttributeFailures:
    """Tests for attribute_failures()."""

    def test_all_pass_no_attribution(self, tmp_path: Path):
        """All cases pass — no failures attributed."""
        results = [
            {"case_id": "c1", "composite_score": 100.0, "step_outputs": {"answer": "yes"}},
            {"case_id": "c2", "composite_score": 100.0, "step_outputs": {"answer": "no"}},
        ]
        results_path = tmp_path / "results.jsonl"
        results_path.write_text(
            "\n".join(json.dumps(r) for r in results), encoding="utf-8"
        )

        attribution = attribute_failures(results_path)
        assert attribution == {}

    def test_retrieval_failure_empty_output(self, tmp_path: Path):
        """Empty retrieval output attributed to retrieval step."""
        results = [
            {
                "case_id": "c1",
                "composite_score": 0.0,
                "context": {"question": "What is Python?"},
                "step_outputs": {"retrieve_docs": "", "answer": "I don't know"},
            },
        ]
        results_path = tmp_path / "results.jsonl"
        results_path.write_text(json.dumps(results[0]), encoding="utf-8")

        attribution = attribute_failures(results_path)
        assert "retrieve_docs" in attribution
        assert attribution["retrieve_docs"]["count"] == 1
        assert "c1" in attribution["retrieve_docs"]["case_ids"]

    def test_retrieval_failure_low_overlap(self, tmp_path: Path):
        """Retrieval output with very low query overlap attributed to retrieval."""
        results = [
            {
                "case_id": "c1",
                "composite_score": 50.0,
                "context": {"question": "capital France geography Europe"},
                "step_outputs": {
                    "search_passages": "banana smoothie recipe blender instructions",
                    "answer": "Unknown",
                },
            },
        ]
        results_path = tmp_path / "results.jsonl"
        results_path.write_text(json.dumps(results[0]), encoding="utf-8")

        attribution = attribute_failures(results_path)
        assert "search_passages" in attribution

    def test_final_step_attribution(self, tmp_path: Path):
        """Good intermediates but wrong final answer attributed to final step."""
        results = [
            {
                "case_id": "c1",
                "composite_score": 0.0,
                "context": {"question": "Is 2+2=4?"},
                "step_outputs": {
                    "summarize": "Basic arithmetic: 2+2=4.",
                    "answer": "no",
                },
            },
        ]
        results_path = tmp_path / "results.jsonl"
        results_path.write_text(json.dumps(results[0]), encoding="utf-8")

        attribution = attribute_failures(results_path)
        assert "answer" in attribution
        assert attribution["answer"]["count"] == 1

    def test_empty_intermediate_step_attribution(self, tmp_path: Path):
        """Empty intermediate step output attributed to that step."""
        results = [
            {
                "case_id": "c1",
                "composite_score": 0.0,
                "context": {"question": "test"},
                "step_outputs": {
                    "step_one": "",
                    "step_two": "some output",
                    "answer": "wrong",
                },
            },
        ]
        results_path = tmp_path / "results.jsonl"
        results_path.write_text(json.dumps(results[0]), encoding="utf-8")

        attribution = attribute_failures(results_path)
        assert "step_one" in attribution

    def test_no_step_outputs(self, tmp_path: Path):
        """Case with no step_outputs attributed to __no_steps__."""
        results = [
            {"case_id": "c1", "composite_score": 0.0},
        ]
        results_path = tmp_path / "results.jsonl"
        results_path.write_text(json.dumps(results[0]), encoding="utf-8")

        attribution = attribute_failures(results_path)
        assert "__no_steps__" in attribution

    def test_multiple_failed_cases(self, tmp_path: Path):
        """Multiple failures accumulate counts per step."""
        results = [
            {
                "case_id": "c1",
                "composite_score": 0.0,
                "context": {"question": "q1"},
                "step_outputs": {"summarize": "ok", "answer": "wrong"},
            },
            {
                "case_id": "c2",
                "composite_score": 0.0,
                "context": {"question": "q2"},
                "step_outputs": {"summarize": "ok", "answer": "also wrong"},
            },
            {
                "case_id": "c3",
                "composite_score": 100.0,
                "step_outputs": {"summarize": "ok", "answer": "correct"},
            },
        ]
        results_path = tmp_path / "results.jsonl"
        results_path.write_text(
            "\n".join(json.dumps(r) for r in results), encoding="utf-8"
        )

        attribution = attribute_failures(results_path)
        assert "answer" in attribution
        assert attribution["answer"]["count"] == 2
        assert set(attribution["answer"]["case_ids"]) == {"c1", "c2"}

    def test_custom_threshold(self, tmp_path: Path):
        """Custom threshold changes which cases are considered failed."""
        results = [
            {
                "case_id": "c1",
                "composite_score": 80.0,
                "context": {"question": "test"},
                "step_outputs": {"answer": "partial"},
            },
        ]
        results_path = tmp_path / "results.jsonl"
        results_path.write_text(json.dumps(results[0]), encoding="utf-8")

        # With default threshold (100), this is a failure
        attr_default = attribute_failures(results_path, threshold=100.0)
        assert "answer" in attr_default

        # With threshold 50, this passes
        attr_low = attribute_failures(results_path, threshold=50.0)
        assert attr_low == {}
