# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the run comparison utility."""

from __future__ import annotations

import json
from pathlib import Path

from src.hephaestus.runs.compare import compare_runs


def _write_results(output_dir: Path, results: list) -> None:
    """Helper: write results.jsonl to a directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.jsonl"
    results_path.write_text(
        "\n".join(json.dumps(r) for r in results), encoding="utf-8"
    )


class TestCompareRuns:
    """Tests for compare_runs()."""

    def test_identical_runs_zero_delta(self, tmp_path: Path):
        """Identical results produce zero deltas."""
        results = [
            {"case_id": "c1", "composite_score": 80.0, "score_breakdown": {"format": 100.0}},
            {"case_id": "c2", "composite_score": 60.0, "score_breakdown": {"format": 80.0}},
        ]
        baseline_dir = tmp_path / "baseline"
        candidate_dir = tmp_path / "candidate"
        _write_results(baseline_dir, results)
        _write_results(candidate_dir, results)

        result = compare_runs(baseline_dir, candidate_dir)
        assert result["composite_delta"]["mean_delta"] == 0.0
        assert result["composite_delta"]["median_delta"] == 0.0
        assert len(result["regressions"]) == 0
        assert len(result["improvements"]) == 0

    def test_candidate_improves(self, tmp_path: Path):
        """Candidate with higher scores shows positive delta."""
        baseline = [
            {"case_id": "c1", "composite_score": 50.0},
            {"case_id": "c2", "composite_score": 50.0},
        ]
        candidate = [
            {"case_id": "c1", "composite_score": 80.0},
            {"case_id": "c2", "composite_score": 90.0},
        ]
        _write_results(tmp_path / "b", baseline)
        _write_results(tmp_path / "c", candidate)

        result = compare_runs(tmp_path / "b", tmp_path / "c")
        assert result["composite_delta"]["mean_delta"] > 0
        assert len(result["improvements"]) == 2
        assert len(result["regressions"]) == 0

    def test_candidate_regresses(self, tmp_path: Path):
        """Candidate with lower scores shows negative delta and regressions."""
        baseline = [
            {"case_id": "c1", "composite_score": 100.0},
        ]
        candidate = [
            {"case_id": "c1", "composite_score": 40.0},
        ]
        _write_results(tmp_path / "b", baseline)
        _write_results(tmp_path / "c", candidate)

        result = compare_runs(tmp_path / "b", tmp_path / "c")
        assert result["composite_delta"]["mean_delta"] < 0
        assert len(result["regressions"]) == 1
        assert result["regressions"][0]["case_id"] == "c1"

    def test_check_deltas(self, tmp_path: Path):
        """Per-check deltas are computed correctly."""
        baseline = [
            {"case_id": "c1", "composite_score": 50.0, "score_breakdown": {"format": 100.0, "accuracy": 0.0}},
        ]
        candidate = [
            {
                "case_id": "c1",
                "composite_score": 75.0,
                "score_breakdown": {"format": 100.0, "accuracy": 50.0},
            },
        ]
        _write_results(tmp_path / "b", baseline)
        _write_results(tmp_path / "c", candidate)

        result = compare_runs(tmp_path / "b", tmp_path / "c")
        assert result["check_deltas"]["format"]["delta"] == 0.0
        assert result["check_deltas"]["accuracy"]["delta"] == 50.0

    def test_timing_deltas(self, tmp_path: Path):
        """Per-step timing deltas are computed."""
        baseline = [
            {"case_id": "c1", "composite_score": 100.0, "step_timings": [["answer", 1.5]]},
        ]
        candidate = [
            {"case_id": "c1", "composite_score": 100.0, "step_timings": [["answer", 0.8]]},
        ]
        _write_results(tmp_path / "b", baseline)
        _write_results(tmp_path / "c", candidate)

        result = compare_runs(tmp_path / "b", tmp_path / "c")
        assert result["timing_deltas"]["answer"]["delta"] < 0

    def test_timing_deltas_repeated_nodes(self, tmp_path: Path):
        """Repeated node names in a trace are aggregated per case."""
        baseline = [
            {
                "case_id": "c1",
                "composite_score": 100.0,
                "step_timings": [["think", 1.0], ["act", 0.5], ["think", 2.0], ["act", 0.3]],
            },
        ]
        candidate = [
            {
                "case_id": "c1",
                "composite_score": 100.0,
                "step_timings": [["think", 0.5], ["act", 0.2]],
            },
        ]
        _write_results(tmp_path / "b", baseline)
        _write_results(tmp_path / "c", candidate)

        result = compare_runs(tmp_path / "b", tmp_path / "c")
        # Baseline think: 1.0+2.0=3.0, candidate think: 0.5
        assert result["timing_deltas"]["think"]["baseline_avg"] == 3.0
        assert result["timing_deltas"]["think"]["candidate_avg"] == 0.5
        assert result["timing_deltas"]["think"]["delta"] < 0

    def test_timing_deltas_old_dict_format(self, tmp_path: Path):
        """Old dict-format step_timings are handled via backwards compat."""
        baseline = [
            {"case_id": "c1", "composite_score": 100.0, "step_timings": {"answer": 1.5}},
        ]
        candidate = [
            {"case_id": "c1", "composite_score": 100.0, "step_timings": [["answer", 0.8]]},
        ]
        _write_results(tmp_path / "b", baseline)
        _write_results(tmp_path / "c", candidate)

        result = compare_runs(tmp_path / "b", tmp_path / "c")
        assert result["timing_deltas"]["answer"]["baseline_avg"] == 1.5
        assert result["timing_deltas"]["answer"]["candidate_avg"] == 0.8

    def test_summary_md_format(self, tmp_path: Path):
        """Summary markdown contains expected sections."""
        baseline = [
            {"case_id": "c1", "composite_score": 50.0, "score_breakdown": {"em": 0.0}},
        ]
        candidate = [
            {"case_id": "c1", "composite_score": 80.0, "score_breakdown": {"em": 100.0}},
        ]
        _write_results(tmp_path / "b", baseline)
        _write_results(tmp_path / "c", candidate)

        result = compare_runs(tmp_path / "b", tmp_path / "c")
        md = result["summary_md"]
        assert "# Run Comparison" in md
        assert "## Composite Score" in md
        assert "## Per-Check Deltas" in md
        assert "Improvements: 1" in md

    def test_mixed_improvements_and_regressions(self, tmp_path: Path):
        """Mixed results identify both improvements and regressions."""
        baseline = [
            {"case_id": "c1", "composite_score": 100.0},
            {"case_id": "c2", "composite_score": 0.0},
        ]
        candidate = [
            {"case_id": "c1", "composite_score": 50.0},
            {"case_id": "c2", "composite_score": 80.0},
        ]
        _write_results(tmp_path / "b", baseline)
        _write_results(tmp_path / "c", candidate)

        result = compare_runs(tmp_path / "b", tmp_path / "c")
        assert len(result["regressions"]) == 1
        assert len(result["improvements"]) == 1
        assert result["regressions"][0]["case_id"] == "c1"
        assert result["improvements"][0]["case_id"] == "c2"
