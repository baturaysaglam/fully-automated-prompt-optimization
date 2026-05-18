# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests that hover eval configs load via load_eval_config."""

from __future__ import annotations

from pathlib import Path

from src.hephaestus.runs.eval_runner import load_eval_config

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"

VAL_CONFIG = "local-chain-variant001.json"


class TestValConfig:
    def test_loads_without_error(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.tenant_id == "hover"

    def test_chain_path(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.chain.path == "tenants/hover/chains/multi_hop.py"

    def test_has_four_prompt_paths(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        prompt_paths = cfg.chain.config.get("prompt_paths", {})
        expected = {"summarize1", "query_hop2", "summarize2", "query_hop3"}
        assert set(prompt_paths.keys()) == expected

    def test_uses_hover_scorer(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.scoring_profile["scorer"]["module_path"].endswith("hover_scorer.py")
