# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests that papillon eval configs load via load_eval_config."""

from __future__ import annotations

from pathlib import Path

from src.hephaestus.runs.eval_runner import load_eval_config

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"

VAL_CONFIG = "local-chain-variant001.json"


class TestValConfig:
    def test_loads_without_error(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.tenant_id == "papillon"

    def test_chain_path(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.chain.path == "tenants/papillon/chains/privacy_chain.py"

    def test_has_two_prompt_paths(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        prompt_paths = cfg.chain.config.get("prompt_paths", {})
        assert set(prompt_paths.keys()) == {"redact_query", "reconstruct_response"}

    def test_uses_papillon_scorer(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.scoring_profile["scorer"]["module_path"].endswith("papillon_scorer.py")

    def test_has_judge_config(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        tc = cfg.scoring_profile.get("tenant_config", {})
        assert "judge_model" in tc
        assert "judge_provider" in tc
