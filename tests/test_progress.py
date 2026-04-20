# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import json
import threading
from pathlib import Path

from src.hephaestus.runs.progress import ProgressTracker, read_progress
from src.hephaestus.types import EvalCaseResult


def _make_result(
    case_id: str = "c1",
    composite_score: float = 80.0,
    breakdown: dict | None = None,
) -> EvalCaseResult:
    return EvalCaseResult(
        case_id=case_id,
        task_type="security",
        diagnostics=[],
        score_breakdown=breakdown or {"quality": 90.0, "format": 70.0},
        composite_score=composite_score,
        output_text="output",
        step_outputs={},
    )


def test_initial_state(tmp_path: Path) -> None:
    tracker = ProgressTracker(tmp_path / "out", total_cases=5)
    snap = tracker.snapshot()
    assert snap.status == "running"
    assert snap.total_cases == 5
    assert snap.completed_cases == 0
    assert snap.avg_composite_score is None
    assert snap.score_breakdown_averages == {}
    assert snap.failed_case_ids == []


def test_record_result_updates_count_and_averages(tmp_path: Path) -> None:
    tracker = ProgressTracker(tmp_path / "out", total_cases=2)

    tracker.record_result(_make_result("c1", 80.0, {"quality": 90.0, "format": 70.0}))
    snap = tracker.snapshot()
    assert snap.completed_cases == 1
    assert snap.avg_composite_score == 80.0
    assert snap.score_breakdown_averages == {"quality": 90.0, "format": 70.0}

    tracker.record_result(_make_result("c2", 60.0, {"quality": 70.0, "format": 50.0}))
    snap = tracker.snapshot()
    assert snap.completed_cases == 2
    assert snap.avg_composite_score == 70.0
    assert snap.score_breakdown_averages == {"quality": 80.0, "format": 60.0}


def test_progress_json_is_valid_after_each_write(tmp_path: Path) -> None:
    out = tmp_path / "out"
    tracker = ProgressTracker(out, total_cases=3)

    data = json.loads((out / "progress.json").read_text(encoding="utf-8"))
    assert data["status"] == "running"
    assert data["completed_cases"] == 0

    tracker.record_result(_make_result())
    data = json.loads((out / "progress.json").read_text(encoding="utf-8"))
    assert data["completed_cases"] == 1


def test_no_lingering_tmp_file(tmp_path: Path) -> None:
    out = tmp_path / "out"
    tracker = ProgressTracker(out, total_cases=1)
    tracker.record_result(_make_result())
    assert not (out / "progress.json.tmp").exists()


def test_mark_completed_sets_status(tmp_path: Path) -> None:
    tracker = ProgressTracker(tmp_path / "out", total_cases=1)
    tracker.record_result(_make_result())
    tracker.mark_completed()
    snap = tracker.snapshot()
    assert snap.status == "completed"


def test_mark_failed_sets_status(tmp_path: Path) -> None:
    tracker = ProgressTracker(tmp_path / "out", total_cases=2)
    tracker.record_result(_make_result())
    tracker.mark_failed()
    snap = tracker.snapshot()
    assert snap.status == "failed"
    assert snap.completed_cases == 1  # Partial progress is preserved


def test_thread_safety_concurrent_records(tmp_path: Path) -> None:
    n = 50
    tracker = ProgressTracker(tmp_path / "out", total_cases=n)

    def record(i: int) -> None:
        tracker.record_result(_make_result(f"c{i}", 100.0, {"q": 100.0}))

    threads = [threading.Thread(target=record, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    snap = tracker.snapshot()
    assert snap.completed_cases == n
    assert snap.avg_composite_score == 100.0


def test_progress_includes_run_id(tmp_path: Path) -> None:
    out = tmp_path / "out"
    tracker = ProgressTracker(out, total_cases=1, run_id="hephaestus-demo-m5kx7r")
    tracker.record_result(_make_result())
    tracker.mark_completed()

    data = json.loads((out / "progress.json").read_text(encoding="utf-8"))
    assert data["run_id"] == "hephaestus-demo-m5kx7r"

    snap = tracker.snapshot()
    assert snap.run_id == "hephaestus-demo-m5kx7r"


def test_read_progress_returns_run_id(tmp_path: Path) -> None:
    out = tmp_path / "out"
    tracker = ProgressTracker(out, total_cases=1, run_id="hephaestus-demo-abc123")
    tracker.record_result(_make_result())
    tracker.mark_completed()

    progress = read_progress(out)
    assert progress is not None
    assert progress.run_id == "hephaestus-demo-abc123"


def test_read_progress_missing_run_id_defaults_empty(tmp_path: Path) -> None:
    """Old progress.json without run_id should default to empty string."""
    out = tmp_path / "out"
    out.mkdir(parents=True)
    data = {
        "status": "completed",
        "total_cases": 1,
        "completed_cases": 1,
        "started_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "avg_composite_score": 80.0,
        "score_breakdown_averages": {},
        "failed_case_ids": [],
    }
    (out / "progress.json").write_text(json.dumps(data), encoding="utf-8")

    progress = read_progress(out)
    assert progress is not None
    assert progress.run_id == ""


def test_read_progress_returns_none_when_missing(tmp_path: Path) -> None:
    assert read_progress(tmp_path / "nonexistent") is None


def test_read_progress_deserializes_written_file(tmp_path: Path) -> None:
    out = tmp_path / "out"
    tracker = ProgressTracker(out, total_cases=2)
    tracker.record_result(_make_result("c1", 90.0, {"quality": 90.0}))
    tracker.mark_completed()

    progress = read_progress(out)
    assert progress is not None
    assert progress.status == "completed"
    assert progress.total_cases == 2
    assert progress.completed_cases == 1
    assert progress.avg_composite_score == 90.0
    assert progress.score_breakdown_averages == {"quality": 90.0}
