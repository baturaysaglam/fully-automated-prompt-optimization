# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for wall-clock duration_seconds in eval output."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from helpers import TrackingProvider, write_dataset, write_scorer

import src.hephaestus.runs.eval_runner as eval_runner
from src.hephaestus.runs.eval_runner import load_eval_config, run_evaluation
from src.hephaestus.runs.progress import ProgressTracker, read_progress
from src.hephaestus.types import EvalCaseResult


def test_run_config_includes_duration_seconds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """run_config.json has a duration_seconds float after successful eval."""
    config_path, out_dir = _write_eval_fixtures(tmp_path)
    monkeypatch.setattr(
        eval_runner, "build_provider_client",
        lambda _p, _s: TrackingProvider(responses=["resp"]),
    )

    run_evaluation(load_eval_config(config_path))

    run_config = json.loads((out_dir / "run_config.json").read_text(encoding="utf-8"))
    assert "duration_seconds" in run_config
    assert isinstance(run_config["duration_seconds"], float)
    assert run_config["duration_seconds"] > 0


def test_progress_json_includes_duration_seconds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """progress.json has a duration_seconds float."""
    config_path, out_dir = _write_eval_fixtures(tmp_path)
    monkeypatch.setattr(
        eval_runner, "build_provider_client",
        lambda _p, _s: TrackingProvider(responses=["resp"]),
    )

    run_evaluation(load_eval_config(config_path))

    progress_data = json.loads((out_dir / "progress.json").read_text(encoding="utf-8"))
    assert "duration_seconds" in progress_data
    assert isinstance(progress_data["duration_seconds"], float)
    assert progress_data["duration_seconds"] > 0


def test_duration_positive_for_successful_eval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Duration > 0 after eval completes."""
    config_path, out_dir = _write_eval_fixtures(tmp_path, cases=3)
    monkeypatch.setattr(
        eval_runner, "build_provider_client",
        lambda _p, _s: TrackingProvider(responses=["resp"]),
    )

    run_evaluation(load_eval_config(config_path))

    run_config = json.loads((out_dir / "run_config.json").read_text(encoding="utf-8"))
    assert run_config["duration_seconds"] > 0


def test_duration_present_on_failed_eval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """progress.json still has duration_seconds when eval fails."""
    config_path, out_dir = _write_eval_fixtures(tmp_path)

    def failing_provider(_p, _s):
        class _FailProvider:
            call_count = 0

            def generate(self, messages, **kwargs):
                raise RuntimeError("Simulated failure")
        return _FailProvider()

    monkeypatch.setattr(eval_runner, "build_provider_client", failing_provider)

    run_evaluation(load_eval_config(config_path))

    progress_data = json.loads((out_dir / "progress.json").read_text(encoding="utf-8"))
    assert "duration_seconds" in progress_data
    assert progress_data["duration_seconds"] >= 0


def test_progress_tracker_duration_increases(tmp_path: Path):
    """ProgressTracker duration_seconds increases over time."""
    out_dir = tmp_path / "out"
    tracker = ProgressTracker(out_dir, total_cases=2)

    progress_1 = json.loads((out_dir / "progress.json").read_text(encoding="utf-8"))
    d1 = progress_1["duration_seconds"]

    time.sleep(0.05)

    tracker.record_result(EvalCaseResult(
        case_id="c1", task_type="test", diagnostics=[],
        score_breakdown={"q": 80.0}, composite_score=80.0,
        output_text="out", step_outputs={},
    ))

    progress_2 = json.loads((out_dir / "progress.json").read_text(encoding="utf-8"))
    d2 = progress_2["duration_seconds"]

    assert d2 > d1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_eval_fixtures(tmp_path: Path, cases: int = 1) -> tuple[Path, Path]:
    dataset = write_dataset(tmp_path, cases=cases)
    scorer = write_scorer(tmp_path)

    template = tmp_path / "template.md"
    template.write_text("User: hello ${inputs.Name}", encoding="utf-8")

    chain_file = tmp_path / "chain.py"
    chain_file.write_text(
        """\
from langgraph.graph import StateGraph, END
from src.hephaestus.chains.nodes import make_llm_node
from pathlib import Path

def build_chain(provider, config):
    prompt_path = Path(config['prompt_paths']['classify'])
    graph = StateGraph(dict)
    graph.add_node('classify', make_llm_node(provider, prompt_path))
    graph.set_entry_point('classify')
    graph.add_edge('classify', END)
    return graph.compile()
""",
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    config = {
        "tenant_id": "demo",
        "provider": "openai",
        "provider_settings": {"model": "gpt-4.1-mini"},
        "dataset": {"path": str(dataset)},
        "chain": {
            "path": str(chain_file),
            "fn": "build_chain",
            "config": {"prompt_paths": {"classify": str(template)}},
        },
        "scoring_profile": {"scorer": {"module_path": str(scorer)}},
        "output_dir": str(out_dir),
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path, out_dir
