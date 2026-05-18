# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests that livebench_math eval configs load via load_eval_config."""

from __future__ import annotations

from pathlib import Path

from src.hephaestus.runs.eval_runner import load_eval_config

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"

VAL_CONFIG = "local-chain-variant001.json"
TEST_CONFIG = "local-chain-variant001-test.json"


class TestValConfig:
    """Tests for the val split config."""

    def test_loads_without_error(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.tenant_id == "livebench_math"

    def test_chain_path_points_to_solve(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.chain.path == "tenants/livebench_math/chains/solve.py"
        assert cfg.chain.fn == "build_chain"

    def test_has_solve_prompt_path(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        prompt_paths = cfg.chain.config.get("prompt_paths", {})
        assert "solve" in prompt_paths

    def test_dataset_path(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.dataset_path == "tenants/livebench_math/datasets/datasets/val.jsonl"

    def test_uses_livebench_math_scorer(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        module_path = cfg.scoring_profile["scorer"]["module_path"]
        assert module_path.endswith("livebench_math_scorer.py")

    def test_provider_is_openai(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.provider == "openai"

    def test_output_dir_under_tenant(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / VAL_CONFIG)
        assert cfg.output_dir.startswith("tenants/livebench_math/evals/")


class TestTestConfig:
    """Tests for the test split config."""

    def test_loads_without_error(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / TEST_CONFIG)
        assert cfg.tenant_id == "livebench_math"

    def test_dataset_points_to_test(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / TEST_CONFIG)
        assert "test.jsonl" in cfg.dataset_path
