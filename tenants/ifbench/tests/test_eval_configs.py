# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests that ifbench eval configs load via load_eval_config."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.hephaestus.runs.eval_runner import load_eval_config

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"

VAL_CONFIG = "local-chain-variant001.json"
TEST_CONFIG = "local-chain-variant001-test.json"


class TestValConfig:
    def test_loads_without_error(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.tenant_id == "ifbench"

    def test_chain_path_points_to_generate_verify(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.chain.path == "tenants/ifbench/chains/generate_verify.py"
        assert cfg.chain.fn == "build_chain"

    def test_has_two_prompt_paths(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        prompt_paths = cfg.chain.config.get("prompt_paths", {})
        assert set(prompt_paths.keys()) == {"generate", "verify"}

    def test_dataset_path(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.dataset_path == "tenants/ifbench/datasets/datasets/val.jsonl"

    def test_uses_ifbench_scorer(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        module_path = cfg.scoring_profile["scorer"]["module_path"]
        assert module_path.endswith("ifbench_scorer.py")

    def test_provider_is_openai(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.provider == "openai"


class TestTestConfig:
    def test_loads_without_error(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / TEST_CONFIG)
        assert cfg.tenant_id == "ifbench"

    def test_dataset_points_to_test(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / TEST_CONFIG)
        assert "test.jsonl" in cfg.dataset_path
