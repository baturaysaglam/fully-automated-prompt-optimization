# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for --model CLI override on the eval subcommand."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from helpers import TrackingProvider, write_dataset, write_scorer

import src.hephaestus.runs.eval_runner as eval_runner
from src.hephaestus.cli import build_parser, main
from src.hephaestus.runs.eval_runner import load_eval_config, run_evaluation


def test_build_parser_accepts_model_flag():
    parser = build_parser()
    args = parser.parse_args(["eval", "--config", "x.json", "--model", "gpt-4o"])
    assert args.model == "gpt-4o"


def test_build_parser_model_default_is_none():
    parser = build_parser()
    args = parser.parse_args(["eval", "--config", "x.json"])
    assert args.model is None


def test_model_override_patches_provider_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """--model gpt-4o patches config.provider_settings before run_evaluation."""
    config_path, _ = _write_eval_fixtures(tmp_path, model="gpt-4.1-mini")

    captured_settings = {}

    def capture_provider(_provider, settings):
        captured_settings.update(settings)
        return TrackingProvider(responses=["resp"])

    monkeypatch.setattr(eval_runner, "build_provider_client", capture_provider)
    monkeypatch.setattr(sys, "argv", [
        "hephaestus", "eval", "--config", str(config_path), "--model", "gpt-4o",
    ])

    main()

    assert captured_settings["model"] == "gpt-4o"


def test_model_override_absent_preserves_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Without --model, config.provider_settings['model'] stays as-is."""
    config_path, _ = _write_eval_fixtures(tmp_path, model="gpt-4.1-mini")

    captured_settings = {}

    def capture_provider(_provider, settings):
        captured_settings.update(settings)
        return TrackingProvider(responses=["resp"])

    monkeypatch.setattr(eval_runner, "build_provider_client", capture_provider)
    monkeypatch.setattr(sys, "argv", [
        "hephaestus", "eval", "--config", str(config_path),
    ])

    main()

    assert captured_settings["model"] == "gpt-4.1-mini"


def test_model_override_with_no_model_in_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """--model works when provider_settings has no model key in the config."""
    config_path, _ = _write_eval_fixtures(tmp_path, model=None)

    captured_settings = {}

    def capture_provider(_provider, settings):
        captured_settings.update(settings)
        return TrackingProvider(responses=["resp"])

    monkeypatch.setattr(eval_runner, "build_provider_client", capture_provider)
    monkeypatch.setattr(sys, "argv", [
        "hephaestus", "eval", "--config", str(config_path), "--model", "gpt-4o-mini",
    ])

    main()

    assert captured_settings["model"] == "gpt-4o-mini"


def test_model_override_flows_to_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Full eval with --model override: provider receives the overridden model."""
    config_path, out_dir = _write_eval_fixtures(tmp_path, model="original-model")

    captured_settings = {}

    def capture_provider(_provider, settings):
        captured_settings.update(settings)
        return TrackingProvider(responses=["resp"])

    monkeypatch.setattr(eval_runner, "build_provider_client", capture_provider)

    config = load_eval_config(config_path)
    config.provider_settings["model"] = "overridden-model"
    run_evaluation(config)

    assert captured_settings["model"] == "overridden-model"

    run_config = json.loads((out_dir / "run_config.json").read_text(encoding="utf-8"))
    assert run_config["provider_settings"]["model"] == "overridden-model"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_eval_fixtures(
    tmp_path: Path,
    model: str | None = "gpt-4.1-mini",
) -> tuple[Path, Path]:
    """Write minimal eval fixtures and return (config_path, output_dir)."""
    dataset = write_dataset(tmp_path, cases=1)
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
    provider_settings: dict = {}
    if model is not None:
        provider_settings["model"] = model

    config = {
        "tenant_id": "demo",
        "provider": "openai",
        "provider_settings": provider_settings,
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
