# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the 1-node CoT solve chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from tenants.livebench_math.chains.solve import build_chain


class _StubProvider:
    """Minimal ProviderClient stub that returns a canned response."""

    def __init__(self, response: str = "stub response") -> None:
        self.response = response
        self.calls: List[List[Dict[str, str]]] = []

    def generate(self, messages: List[Dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.response


@pytest.fixture()
def prompt_file(tmp_path: Path) -> Path:
    """Create a minimal prompt template."""
    p = tmp_path / "variant-001.md"
    p.write_text("System: Solve the math problem.\n\nUser: ${question}")
    return p


def _build_config(prompt_file: Path) -> Dict[str, Any]:
    return {"prompt_paths": {"solve": str(prompt_file)}}


class TestBuildChain:
    """Tests for the build_chain factory function."""

    def test_chain_compiles(self, prompt_file: Path) -> None:
        """build_chain returns a compiled graph with invoke method."""
        provider = _StubProvider()
        config = _build_config(prompt_file)
        chain = build_chain(provider, config)
        assert hasattr(chain, "invoke")

    def test_chain_has_1_node(self, prompt_file: Path) -> None:
        """The compiled chain has exactly 1 node (excluding __start__/__end__)."""
        provider = _StubProvider()
        config = _build_config(prompt_file)
        chain = build_chain(provider, config)

        graph = chain.get_graph()
        node_names = {n for n in graph.nodes if n not in ("__start__", "__end__")}
        assert node_names == {"solve"}

    def test_chain_invokes_provider_once(self, prompt_file: Path) -> None:
        """Chain execution should call the provider exactly once."""
        provider = _StubProvider(response="The answer is \\boxed{42}")
        config = _build_config(prompt_file)
        chain = build_chain(provider, config)

        result = chain.invoke({
            "context": {"question": "What is 6 times 7?"},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        })

        assert len(provider.calls) == 1
        assert result["output_text"] == "The answer is \\boxed{42}"

    def test_chain_sets_step_outputs(self, prompt_file: Path) -> None:
        """Chain should populate step_outputs with 'output_text' key (default)."""
        provider = _StubProvider(response="answer: 100")
        config = _build_config(prompt_file)
        chain = build_chain(provider, config)

        result = chain.invoke({
            "context": {"question": "Compute 10^2"},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        })

        assert "output_text" in result["step_outputs"]
