# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _normalize_timings(timings: Any) -> List[List]:
    """Convert step_timings to list-of-lists format (handles old dict format)."""
    if isinstance(timings, dict):
        return [[k, v] for k, v in timings.items()]
    return timings or []


def write_outputs(output_dir: Path, run_config: Dict, results: Iterable[Dict]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    run_config_path = output_dir / "run_config.json"
    results_path = output_dir / "results.jsonl"
    summary_path = output_dir / "summary.md"

    run_config_path.write_text(json.dumps(run_config, indent=2), encoding="utf-8")

    results_list: List[Dict] = list(results)
    with results_path.open("w", encoding="utf-8") as handle:
        for item in results_list:
            handle.write(json.dumps(item) + "\n")

    total = len(results_list)
    scores: List[float] = []
    breakdown_totals: Dict[str, float] = {}
    for item in results_list:
        scores.append(float(item.get("composite_score", 0.0)))
        for key, value in item.get("score_breakdown", {}).items():
            breakdown_totals[key] = breakdown_totals.get(key, 0.0) + float(value)

    lines = ["# Evaluation Summary", "", f"Total cases: {total}", ""]
    if scores:
        lines.append("## Composite Score")
        lines.append(f"- average: {sum(scores)/len(scores):.2f}")
        lines.append("")
    if breakdown_totals:
        lines.append("## Score Breakdown")
        for key in sorted(breakdown_totals):
            average = breakdown_totals[key] / total if total else 0.0
            lines.append(f"- {key}: {average:.2f}")

    # Point-weighted score (for scoring schemes with earned/possible points)
    if "points_earned" in breakdown_totals and "points_possible" in breakdown_totals:
        total_earned = breakdown_totals["points_earned"]
        total_possible = breakdown_totals["points_possible"]
        weighted_score = (total_earned / total_possible * 100.0) if total_possible > 0 else 0.0
        lines.append("")
        lines.append("## Weighted Score")
        lines.append(f"- weighted_score: {weighted_score:.2f}")
        lines.append(f"- total_earned: {total_earned:.0f}")
        lines.append(f"- total_possible: {total_possible:.0f}")

    # Step timings section
    step_timings_by_name: Dict[str, List[float]] = {}
    case_totals: List[float] = []
    for item in results_list:
        trace = _normalize_timings(item.get("step_timings"))
        if trace:
            case_totals.append(sum(d for _, d in trace))
            for step_name, duration in trace:
                step_timings_by_name.setdefault(step_name, []).append(duration)

    if step_timings_by_name:
        lines.append("")
        lines.append("## Step Timings")
        lines.append("")
        lines.append("| Step | Avg (s) | P50 (s) | P95 (s) |")
        lines.append("|------|---------|---------|---------|")
        for step_name in step_timings_by_name:
            vals = step_timings_by_name[step_name]
            avg = statistics.mean(vals)
            p50 = statistics.median(vals)
            p95 = sorted(vals)[int(math.ceil(len(vals) * 0.95)) - 1] if len(vals) > 1 else vals[0]
            lines.append(f"| {step_name} | {avg:.3f} | {p50:.3f} | {p95:.3f} |")
        if case_totals:
            avg_total = statistics.mean(case_totals)
            p50_total = statistics.median(case_totals)
            p95_total = (
                sorted(case_totals)[int(math.ceil(len(case_totals) * 0.95)) - 1]
                if len(case_totals) > 1
                else case_totals[0]
            )
            lines.append(f"| **Total** | **{avg_total:.3f}** | **{p50_total:.3f}** | **{p95_total:.3f}** |")

    # Step attribution section — only when there are failures with step_outputs
    has_step_outputs = any(item.get("step_outputs") for item in results_list)
    has_failures = any(float(item.get("composite_score", 0)) < 100.0 for item in results_list)
    if has_step_outputs and has_failures:
        import tempfile

        from src.hephaestus.analysis.step_attribution import attribute_failures

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as tf:
            for item in results_list:
                tf.write(json.dumps(item) + "\n")
            tf_path = Path(tf.name)

        try:
            attribution = attribute_failures(tf_path)
            if attribution:
                lines.append("")
                lines.append("## Step Attribution")
                lines.append("")
                lines.append("| Step | Failure Count |")
                lines.append("|------|--------------|")
                for step_name in sorted(attribution, key=lambda s: attribution[s]["count"], reverse=True):
                    lines.append(f"| {step_name} | {attribution[step_name]['count']} |")
        finally:
            tf_path.unlink(missing_ok=True)

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
