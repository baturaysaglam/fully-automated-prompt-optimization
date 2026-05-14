# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the 2-node generate→verify chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from tenants.ifbench.chains.generate_verify import build_chain


class _StubProvider:
    """Minimal ProviderClient stub."""

    def __init__(self, response: str = "stub response") -> None:
        self.response = response
        self.calls: List[List[Dict[str, str]]] = []

    def generate(self, messages: List[Dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.response


@pytest.fixture()
def prompt_dir(tmp_path: Path) -> Path:
    """Create minimal prompt templates."""
    gen = tmp_path / "generate" / "variant-001.md"
    gen.parent.mkdir(parents=True)
    gen.write_text("System: Generate response\n\nUser: ${prompt}")

    ver = tmp_path / "verify" / "variant-001.md"
    ver.parent.mkdir(parents=True)
    ver.write_text(
        "System: Verify response\n\n"
        "User: ${prompt} ${steps.generate.output}"
    )
    return tmp_path


def _build_config(prompt_dir: Path) -> Dict[str, Any]:
    return {
        "prompt_paths": {
            "generate": str(prompt_dir / "generate" / "variant-001.md"),
            "verify": str(prompt_dir / "verify" / "variant-001.md"),
        }
    }


class TestBuildChain:
    def test_chain_compiles(self, prompt_dir: Path) -> None:
        provider = _StubProvider()
        chain = build_chain(provider, _build_config(prompt_dir))
        assert hasattr(chain, "invoke")

    def test_chain_has_2_nodes(self, prompt_dir: Path) -> None:
        provider = _StubProvider()
        chain = build_chain(provider, _build_config(prompt_dir))
        graph = chain.get_graph()
        node_names = {n for n in graph.nodes if n not in ("__start__", "__end__")}
        assert node_names == {"generate", "verify"}

    def test_chain_invokes_provider_twice(self, prompt_dir: Path) -> None:
        provider = _StubProvider(response="mock output")
        chain = build_chain(provider, _build_config(prompt_dir))

        result = chain.invoke({
            "context": {"prompt": "Write a poem with exactly 5 lines."},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        })

        assert len(provider.calls) == 2
        assert result["output_text"] == "mock output"

    def test_verify_receives_generate_output(self, prompt_dir: Path) -> None:
        """The verify node should have access to generate's output via step_outputs."""
        responses = iter(["first response", "final response"])
        provider = _StubProvider()
        provider.generate = lambda msgs: next(responses)

        chain = build_chain(provider, _build_config(prompt_dir))

        result = chain.invoke({
            "context": {"prompt": "Test prompt"},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        })

        assert result["step_outputs"]["generate"] == "first response"
        assert result["step_outputs"]["verify"] == "final response"
        assert result["output_text"] == "final response"
