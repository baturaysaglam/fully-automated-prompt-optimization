# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.hephaestus.types import EvalCaseResult, EvalProgress


class ProgressTracker:
    """Thread-safe tracker that writes ``progress.json`` after each case."""

    def __init__(self, output_dir: Path, total_cases: int, run_id: str = "") -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

        now = datetime.now(timezone.utc).isoformat()
        self._progress = EvalProgress(
            status="running",
            total_cases=total_cases,
            completed_cases=0,
            started_at=now,
            updated_at=now,
            avg_composite_score=None,
            score_breakdown_averages={},
            failed_case_ids=[],
            run_id=run_id,
        )
        self._score_sum: float = 0.0
        self._breakdown_sums: dict[str, float] = {}
        self._points_earned_sum: float = 0.0
        self._points_possible_sum: float = 0.0
        self._write()

    def record_start(self, case_id: str) -> None:
        """Mark a case as in-flight."""
        with self._lock:
            self._progress.in_flight_case_ids.append(case_id)
            self._progress.updated_at = datetime.now(timezone.utc).isoformat()
            self._write()

    def record_result(self, result: EvalCaseResult) -> None:
        with self._lock:
            if result.case_id in self._progress.in_flight_case_ids:
                self._progress.in_flight_case_ids.remove(result.case_id)
            self._progress.completed_cases += 1
            self._score_sum += result.composite_score
            self._progress.avg_composite_score = (
                self._score_sum / self._progress.completed_cases
            )

            for key, value in result.score_breakdown.items():
                if isinstance(value, (int, float)):
                    self._breakdown_sums[key] = self._breakdown_sums.get(key, 0.0) + value
            self._progress.score_breakdown_averages = {
                k: v / self._progress.completed_cases
                for k, v in self._breakdown_sums.items()
            }

            # Track point-weighted score for point-based scoring schemes
            bd = result.score_breakdown
            if "points_earned" in bd and "points_possible" in bd:
                self._points_earned_sum += float(bd["points_earned"])
                self._points_possible_sum += float(bd["points_possible"])

            self._progress.updated_at = datetime.now(timezone.utc).isoformat()
            self._write()

    def mark_completed(self) -> None:
        with self._lock:
            self._progress.status = "completed"
            self._progress.updated_at = datetime.now(timezone.utc).isoformat()
            self._write()

    def mark_failed(self) -> None:
        with self._lock:
            self._progress.status = "failed"
            self._progress.updated_at = datetime.now(timezone.utc).isoformat()
            self._write()

    def snapshot(self) -> EvalProgress:
        with self._lock:
            return EvalProgress(
                status=self._progress.status,
                total_cases=self._progress.total_cases,
                completed_cases=self._progress.completed_cases,
                started_at=self._progress.started_at,
                updated_at=self._progress.updated_at,
                avg_composite_score=self._progress.avg_composite_score,
                score_breakdown_averages=dict(self._progress.score_breakdown_averages),
                failed_case_ids=list(self._progress.failed_case_ids),
                in_flight_case_ids=list(self._progress.in_flight_case_ids),
                run_id=self._progress.run_id,
            )

    def _write(self) -> None:
        """Write progress atomically via tmp + os.replace."""
        weighted_avg = (
            (self._points_earned_sum / self._points_possible_sum * 100.0)
            if self._points_possible_sum > 0
            else None
        )
        data = {
            "run_id": self._progress.run_id,
            "status": self._progress.status,
            "total_cases": self._progress.total_cases,
            "completed_cases": self._progress.completed_cases,
            "started_at": self._progress.started_at,
            "updated_at": self._progress.updated_at,
            "avg_composite_score": self._progress.avg_composite_score,
            "weighted_avg_score": weighted_avg,
            "score_breakdown_averages": self._progress.score_breakdown_averages,
            "failed_case_ids": self._progress.failed_case_ids,
            "in_flight_case_ids": self._progress.in_flight_case_ids,
        }
        tmp_path = self._output_dir / "progress.json.tmp"
        final_path = self._output_dir / "progress.json"
        tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp_path, final_path)


def read_progress(output_dir: Path) -> Optional[EvalProgress]:
    """Read and deserialize ``progress.json``. Returns ``None`` if missing."""
    path = output_dir / "progress.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return EvalProgress(
        status=data["status"],
        total_cases=data["total_cases"],
        completed_cases=data["completed_cases"],
        started_at=data["started_at"],
        updated_at=data["updated_at"],
        avg_composite_score=data["avg_composite_score"],
        score_breakdown_averages=data.get("score_breakdown_averages", {}),
        failed_case_ids=data.get("failed_case_ids", []),
        in_flight_case_ids=data.get("in_flight_case_ids", []),
        run_id=data.get("run_id", ""),
    )
