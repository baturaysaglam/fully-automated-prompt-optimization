# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for chain types: ChainConfig, ChainState, and EvalConfig chain field."""

from __future__ import annotations

import pytest

from src.hephaestus.chains.types import ChainState
from src.hephaestus.types import ChainConfig, EvalConfig


class TestChainConfig:
    def test_chain_config_construction(self) -> None:
        """ChainConfig can be constructed with all fields explicitly."""
        cfg = ChainConfig(
            path="tenants/acme/chains/classify.py",
            fn="my_build_chain",
            config={"prompt_paths": {"classify": "prompts/v1.md"}},
        )
        assert cfg.path == "tenants/acme/chains/classify.py"
        assert cfg.fn == "my_build_chain"
        assert cfg.config == {"prompt_paths": {"classify": "prompts/v1.md"}}

    def test_chain_config_defaults(self) -> None:
        """fn defaults to 'build_chain' and config defaults to empty dict."""
        cfg = ChainConfig(path="chains/foo.py")
        assert cfg.fn == "build_chain"
        assert cfg.config == {}


class TestChainState:
    def test_chain_state_type_checking(self) -> None:
        """ChainState TypedDict accepts the correct field types."""
        state: ChainState = {
            "context": {"question": "What is 2+2?"},
            "output_text": "4",
            "step_outputs": {"step1": "intermediate"},
        }
        assert state["context"] == {"question": "What is 2+2?"}
        assert state["output_text"] == "4"
        assert state["step_outputs"] == {"step1": "intermediate"}


class TestEvalConfigChainField:
    def test_eval_config_requires_chain(self) -> None:
        """EvalConfig without chain raises TypeError (chain is required)."""
        with pytest.raises(TypeError):
            EvalConfig(
                tenant_id="acme",
                provider="baseten",
                provider_settings={"model_id": "abc"},
                dataset_path="data/cases.jsonl",
                scoring_profile={"scorer": {}},
                output_dir="output/",
            )  # type: ignore[call-arg]

    def test_eval_config_with_chain(self) -> None:
        """EvalConfig with ChainConfig populated."""
        chain_cfg = ChainConfig(
            path="chains/classify.py",
            fn="build_chain",
            config={"prompt_paths": {"classify": "prompts/v1.md"}},
        )
        cfg = EvalConfig(
            tenant_id="acme",
            provider="baseten",
            provider_settings={"model_id": "abc"},
            dataset_path="data/cases.jsonl",
            scoring_profile={"scorer": {}},
            output_dir="output/",
            chain=chain_cfg,
        )
        assert cfg.chain.path == "chains/classify.py"
        assert cfg.chain.fn == "build_chain"
        assert cfg.chain.config == {"prompt_paths": {"classify": "prompts/v1.md"}}
