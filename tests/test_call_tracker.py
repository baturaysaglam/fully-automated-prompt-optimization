# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for src/hephaestus/optimization/call_tracker.py."""

from __future__ import annotations

import concurrent.futures
import dataclasses
import json
from pathlib import Path
from typing import Dict

from src.hephaestus.optimization.call_tracker import (
    CallEvent,
    CallSummary,
    append_event,
    summarize,
)


def _ev(
    idx: int,
    *,
    event: str = "invocation_start",
    subagent: str = "optimization",
    layer: str = "orchestrator",
    model_family: str = "opus",
    model_id: str = "opus",
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    duration_ms: int | None = None,
) -> CallEvent:
    return CallEvent(
        timestamp=f"2026-05-08T00:00:{idx:02d}Z",
        run_id="run-xyz",
        tenant_id="hotpotqa",
        layer=layer,
        subagent=subagent,
        model_family=model_family,
        model_id=model_id,
        event=event,
        invocation_id=f"inv-{idx}",
        parent_invocation_id=None,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
    )


# --- append_event ---


def test_append_event_creates_directory(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "optimization-calls.jsonl"
    append_event(path, _ev(1))
    assert path.exists()
    assert path.read_text().count("\n") == 1


def test_append_event_appends_single_line_per_event(tmp_path: Path) -> None:
    path = tmp_path / "calls.jsonl"
    for i in range(5):
        append_event(path, _ev(i))
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    assert len(lines) == 5
    for i, ln in enumerate(lines):
        parsed = json.loads(ln)
        assert parsed["invocation_id"] == f"inv-{i}"


def test_append_event_under_concurrent_threads(tmp_path: Path) -> None:
    """10 parallel threads append 20 events total; all 20 lines land intact."""
    path = tmp_path / "calls.jsonl"
    N = 20

    def append_one(i: int) -> None:
        append_event(path, _ev(i))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(append_one, range(N)))

    raw = path.read_text()
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    assert len(lines) == N
    # All lines parse as JSON (atomicity holds).
    for ln in lines:
        json.loads(ln)


# --- CallEvent round-trip ---


def test_call_event_json_round_trip() -> None:
    original = _ev(1, input_tokens=42, output_tokens=7, duration_ms=1000)
    serialized = json.dumps(dataclasses.asdict(original), sort_keys=True)
    parsed = json.loads(serialized)
    rebuilt = CallEvent(**parsed)
    assert rebuilt == original


# --- summarize ---


def test_summarize_empty_path(tmp_path: Path) -> None:
    summary = summarize(tmp_path / "does-not-exist.jsonl")
    assert summary.total == 0
    assert summary.by_subagent == {}


def test_summarize_counts_start_events_only(tmp_path: Path) -> None:
    """Invocation totals should equal the number of *start* events, not pairs."""
    path = tmp_path / "calls.jsonl"
    # 3 pairs → 3 start + 3 end = 6 lines, but total == 3
    for i in range(3):
        append_event(path, _ev(i, event="invocation_start"))
        append_event(path, _ev(i, event="invocation_end", input_tokens=10, output_tokens=5, duration_ms=100))
    summary = summarize(path)
    assert summary.total == 3
    assert summary.input_tokens == 30
    assert summary.output_tokens == 15
    assert summary.duration_ms_total == 300


def test_summarize_aggregation_by_dim(tmp_path: Path) -> None:
    path = tmp_path / "calls.jsonl"
    # 4 optimization (opus, orchestrator), 2 variant-reviewer (opus, subagent),
    # 3 step-attribution (sonnet, subagent)
    for i in range(4):
        append_event(
            path,
            _ev(
                i,
                event="invocation_start",
                subagent="optimization",
                layer="orchestrator",
                model_family="opus",
                model_id="opus",
            ),
        )
    for i in range(2):
        append_event(
            path,
            _ev(
                100 + i,
                event="invocation_start",
                subagent="variant-reviewer",
                layer="subagent",
                model_family="opus",
                model_id="opus",
            ),
        )
    for i in range(3):
        append_event(
            path,
            _ev(
                200 + i,
                event="invocation_start",
                subagent="step-attribution",
                layer="subagent",
                model_family="sonnet",
                model_id="sonnet",
            ),
        )

    summary = summarize(path)
    assert summary.total == 9
    assert summary.by_subagent == {"optimization": 4, "variant-reviewer": 2, "step-attribution": 3}
    assert summary.by_layer == {"orchestrator": 4, "subagent": 5}
    assert summary.by_model_family == {"opus": 6, "sonnet": 3}
    assert summary.by_model_id == {"opus": 6, "sonnet": 3}


def test_summarize_preserves_unknown_model_id(tmp_path: Path) -> None:
    """Forward-compat: unknown model ids/families are preserved verbatim."""
    path = tmp_path / "calls.jsonl"
    append_event(path, _ev(0, event="invocation_start", model_family="new-family", model_id="new-family-4"))
    summary = summarize(path)
    assert summary.by_model_family == {"new-family": 1}
    assert summary.by_model_id == {"new-family-4": 1}


def test_summarize_skips_malformed_lines(tmp_path: Path) -> None:
    """A truncated final line should not crash the summarizer."""
    path = tmp_path / "calls.jsonl"
    append_event(path, _ev(0, event="invocation_start"))
    # Simulate a crash mid-write with a garbled trailing line.
    with path.open("a", encoding="utf-8") as f:
        f.write('{"timestamp": "2026-05-08T0')
    summary = summarize(path)
    assert summary.total == 1  # malformed line ignored


# --- CallSummary.to_dict structure ---


def test_call_summary_to_dict_shape() -> None:
    s = CallSummary(
        total=3,
        by_subagent={"a": 1, "b": 2},
        by_layer={"orchestrator": 1, "subagent": 2},
        by_model_family={"opus": 3},
        by_model_id={"opus": 3},
        input_tokens=100,
        output_tokens=50,
        duration_ms_total=2000,
    )
    out: Dict = s.to_dict()
    assert out["total"] == 3
    assert out["tokens"] == {"input": 100, "output": 50}
    assert out["duration_ms_total"] == 2000
    assert out["by_model_family"] == {"opus": 3}
