# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests that HotpotQA eval configs load via load_eval_config."""

from __future__ import annotations

from pathlib import Path

from src.hephaestus.runs.eval_runner import load_eval_config

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"

FULL_CHAIN_CONFIG = "local-chain-variant001.json"


class TestFullChainConfig:
    """Tests for the full 6-node chain config."""

    def test_loads_without_error(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / FULL_CHAIN_CONFIG)
        assert cfg.tenant_id == "hotpotqa"

    def test_chain_path_points_to_multi_hop(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / FULL_CHAIN_CONFIG)
        assert cfg.chain.path == "tenants/hotpotqa/chains/multi_hop.py"
        assert cfg.chain.fn == "build_chain"

    def test_has_four_prompt_paths(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / FULL_CHAIN_CONFIG)
        prompt_paths = cfg.chain.config.get("prompt_paths", {})
        expected_keys = {
            "generate_query_with_context",
            "summarize1",
            "summarize2",
            "generate_answer",
        }
        assert set(prompt_paths.keys()) == expected_keys

    def test_dataset_path(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / FULL_CHAIN_CONFIG)
        assert cfg.dataset_path == "tenants/hotpotqa/datasets/datasets/val.jsonl"

    def test_uses_hotpotqa_scorer(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / FULL_CHAIN_CONFIG)
        module_path = cfg.scoring_profile["scorer"]["module_path"]
        assert module_path.endswith("hotpotqa_scorer.py")

    def test_provider_is_openai(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / FULL_CHAIN_CONFIG)
        assert cfg.provider == "openai"

    def test_output_dir_under_tenant(self) -> None:
        cfg = load_eval_config(CONFIGS_DIR / FULL_CHAIN_CONFIG)
        assert cfg.output_dir.startswith("tenants/hotpotqa/evals/")
