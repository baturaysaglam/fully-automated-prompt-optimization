# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Comparison utility for two eval output directories.

Produces composite score deltas, per-check deltas, per-step timing deltas,
case-level regressions/improvements, and a markdown summary.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.hephaestus.runs.io_utils import _normalize_timings


def _load_results(output_dir: Path) -> List[Dict[str, Any]]:
    """Load results.jsonl from an eval output directory."""
    results_path = output_dir / "results.jsonl"
    results: List[Dict[str, Any]] = []
    with results_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def compare_runs(
    baseline_dir: Path,
    candidate_dir: Path,
) -> Dict[str, Any]:
    """Compare two eval output directories.

    Args:
        baseline_dir: Path to baseline eval output directory.
        candidate_dir: Path to candidate eval output directory.

    Returns:
        Dict with keys: composite_delta, check_deltas, timing_deltas,
        regressions, improvements, summary_md.
    """
    baseline = _load_results(baseline_dir)
    candidate = _load_results(candidate_dir)

    baseline_by_id = {r.get("case_id", i): r for i, r in enumerate(baseline)}
    candidate_by_id = {r.get("case_id", i): r for i, r in enumerate(candidate)}

    # Composite score delta
    baseline_scores = [float(r.get("composite_score", 0)) for r in baseline]
    candidate_scores = [float(r.get("composite_score", 0)) for r in candidate]

    composite_delta = _score_delta(baseline_scores, candidate_scores)

    # Per-check score delta
    check_deltas = _check_deltas(baseline, candidate)

    # Per-step timing delta
    timing_deltas = _timing_deltas(baseline, candidate)

    # Case-level regressions and improvements
    regressions, improvements = _case_changes(baseline_by_id, candidate_by_id)

    summary_md = _build_summary(
        composite_delta, check_deltas, timing_deltas, regressions, improvements
    )

    return {
        "composite_delta": composite_delta,
        "check_deltas": check_deltas,
        "timing_deltas": timing_deltas,
        "regressions": regressions,
        "improvements": improvements,
        "summary_md": summary_md,
    }


def _score_delta(
    baseline_scores: List[float], candidate_scores: List[float]
) -> Dict[str, float]:
    """Compute mean and median delta between two score lists."""
    b_mean = statistics.mean(baseline_scores) if baseline_scores else 0.0
    c_mean = statistics.mean(candidate_scores) if candidate_scores else 0.0
    b_median = statistics.median(baseline_scores) if baseline_scores else 0.0
    c_median = statistics.median(candidate_scores) if candidate_scores else 0.0
    return {
        "baseline_mean": b_mean,
        "candidate_mean": c_mean,
        "mean_delta": c_mean - b_mean,
        "baseline_median": b_median,
        "candidate_median": c_median,
        "median_delta": c_median - b_median,
    }


def _check_deltas(
    baseline: List[Dict[str, Any]], candidate: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """Compute per-check average score deltas."""
    baseline_checks: Dict[str, List[float]] = {}
    candidate_checks: Dict[str, List[float]] = {}

    for r in baseline:
        for k, v in r.get("score_breakdown", {}).items():
            baseline_checks.setdefault(k, []).append(float(v))
    for r in candidate:
        for k, v in r.get("score_breakdown", {}).items():
            candidate_checks.setdefault(k, []).append(float(v))

    all_checks = sorted(set(baseline_checks) | set(candidate_checks))
    deltas: Dict[str, Dict[str, float]] = {}
    for check in all_checks:
        b_avg = statistics.mean(baseline_checks[check]) if check in baseline_checks else 0.0
        c_avg = statistics.mean(candidate_checks[check]) if check in candidate_checks else 0.0
        deltas[check] = {
            "baseline_avg": b_avg,
            "candidate_avg": c_avg,
            "delta": c_avg - b_avg,
        }
    return deltas


def _aggregate_timings_per_case(trace: List[List]) -> Dict[str, float]:
    """Sum durations by node name within a single case's trace."""
    totals: Dict[str, float] = {}
    for name, duration in trace:
        totals[name] = totals.get(name, 0.0) + float(duration)
    return totals


def _timing_deltas(
    baseline: List[Dict[str, Any]], candidate: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """Compute per-step average timing deltas."""
    baseline_timings: Dict[str, List[float]] = {}
    candidate_timings: Dict[str, List[float]] = {}

    for r in baseline:
        per_case = _aggregate_timings_per_case(_normalize_timings(r.get("step_timings")))
        for k, v in per_case.items():
            baseline_timings.setdefault(k, []).append(v)
    for r in candidate:
        per_case = _aggregate_timings_per_case(_normalize_timings(r.get("step_timings")))
        for k, v in per_case.items():
            candidate_timings.setdefault(k, []).append(v)

    all_steps = sorted(set(baseline_timings) | set(candidate_timings))
    deltas: Dict[str, Dict[str, float]] = {}
    for step in all_steps:
        b_avg = statistics.mean(baseline_timings[step]) if step in baseline_timings else 0.0
        c_avg = statistics.mean(candidate_timings[step]) if step in candidate_timings else 0.0
        deltas[step] = {
            "baseline_avg": b_avg,
            "candidate_avg": c_avg,
            "delta": c_avg - b_avg,
        }
    return deltas


def _case_changes(
    baseline_by_id: Dict[str, Dict[str, Any]],
    candidate_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Identify regressions and improvements at the case level."""
    common_ids = sorted(set(baseline_by_id) & set(candidate_by_id))
    regressions: List[Dict[str, Any]] = []
    improvements: List[Dict[str, Any]] = []

    for cid in common_ids:
        b_score = float(baseline_by_id[cid].get("composite_score", 0))
        c_score = float(candidate_by_id[cid].get("composite_score", 0))
        delta = c_score - b_score
        entry = {"case_id": cid, "baseline_score": b_score, "candidate_score": c_score, "delta": delta}
        if delta < 0:
            regressions.append(entry)
        elif delta > 0:
            improvements.append(entry)

    regressions.sort(key=lambda x: x["delta"])
    improvements.sort(key=lambda x: x["delta"], reverse=True)
    return regressions, improvements


def _build_summary(
    composite_delta: Dict[str, float],
    check_deltas: Dict[str, Dict[str, float]],
    timing_deltas: Dict[str, Dict[str, float]],
    regressions: List[Dict[str, Any]],
    improvements: List[Dict[str, Any]],
) -> str:
    """Build a markdown summary of the comparison."""
    lines = ["# Run Comparison", ""]

    lines.append("## Composite Score")
    lines.append(f"- Baseline mean: {composite_delta['baseline_mean']:.2f}")
    lines.append(f"- Candidate mean: {composite_delta['candidate_mean']:.2f}")
    lines.append(f"- Mean delta: {composite_delta['mean_delta']:+.2f}")
    lines.append(f"- Median delta: {composite_delta['median_delta']:+.2f}")
    lines.append("")

    if check_deltas:
        lines.append("## Per-Check Deltas")
        lines.append("")
        lines.append("| Check | Baseline | Candidate | Delta |")
        lines.append("|-------|----------|-----------|-------|")
        for check, vals in sorted(check_deltas.items()):
            lines.append(
                f"| {check} | {vals['baseline_avg']:.2f} "
                f"| {vals['candidate_avg']:.2f} | {vals['delta']:+.2f} |"
            )
        lines.append("")

    if timing_deltas:
        lines.append("## Per-Step Timing Deltas")
        lines.append("")
        lines.append("| Step | Baseline (s) | Candidate (s) | Delta (s) |")
        lines.append("|------|-------------|--------------|-----------|")
        for step, vals in sorted(timing_deltas.items()):
            lines.append(
                f"| {step} | {vals['baseline_avg']:.3f} "
                f"| {vals['candidate_avg']:.3f} | {vals['delta']:+.3f} |"
            )
        lines.append("")

    lines.append("## Case Changes")
    lines.append(f"- Improvements: {len(improvements)}")
    lines.append(f"- Regressions: {len(regressions)}")

    if regressions:
        lines.append("")
        lines.append("### Top Regressions")
        for r in regressions[:5]:
            lines.append(
                f"- `{r['case_id']}`: {r['baseline_score']:.0f} -> "
                f"{r['candidate_score']:.0f} ({r['delta']:+.0f})"
            )

    if improvements:
        lines.append("")
        lines.append("### Top Improvements")
        for imp in improvements[:5]:
            lines.append(
                f"- `{imp['case_id']}`: {imp['baseline_score']:.0f} -> "
                f"{imp['candidate_score']:.0f} ({imp['delta']:+.0f})"
            )

    return "\n".join(lines) + "\n"
