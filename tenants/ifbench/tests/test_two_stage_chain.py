# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the ifbench 2-node chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from tenants.ifbench.chains.two_stage import build_chain


class _StubProvider:
    def __init__(self, responses: List[str] | None = None) -> None:
        self.responses = responses or ["draft", "revised"]
        self.call_index = 0
        self.calls: List[List[Dict[str, str]]] = []

    def generate(self, messages: List[Dict[str, str]]) -> str:
        self.calls.append(messages)
        resp = self.responses[min(self.call_index, len(self.responses) - 1)]
        self.call_index += 1
        return resp


@pytest.fixture()
def prompt_dir(tmp_path: Path) -> Path:
    modules = {
        "generate_response": "System: draft\n\nUser: ${prompt}",
        "ensure_correct_response": "System: revise\n\nUser: ${prompt} ${steps.generate_response.output}",
    }
    for name, content in modules.items():
        p = tmp_path / name / "variant-001.md"
        p.parent.mkdir(parents=True)
        p.write_text(content, encoding="utf-8")
    return tmp_path


def _build_config(prompt_dir: Path) -> Dict[str, Any]:
    return {
        "prompt_paths": {
            "generate_response": str(prompt_dir / "generate_response" / "variant-001.md"),
            "ensure_correct_response": str(prompt_dir / "ensure_correct_response" / "variant-001.md"),
        }
    }


def test_chain_compiles(prompt_dir: Path) -> None:
    chain = build_chain(_StubProvider(), _build_config(prompt_dir))
    assert hasattr(chain, "invoke")


def test_chain_has_2_nodes(prompt_dir: Path) -> None:
    chain = build_chain(_StubProvider(), _build_config(prompt_dir))
    node_names = {n for n in chain.get_graph().nodes if n not in ("__start__", "__end__")}
    assert node_names == {"generate_response", "ensure_correct_response"}


def test_chain_two_provider_calls_in_order(prompt_dir: Path) -> None:
    provider = _StubProvider(responses=["draft-resp", "revised-resp"])
    chain = build_chain(provider, _build_config(prompt_dir))
    result = chain.invoke(
        {
            "context": {"prompt": "Write a response."},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        }
    )
    assert len(provider.calls) == 2
    assert result["step_outputs"]["generate_response"] == "draft-resp"
    assert result["step_outputs"]["ensure_correct_response"] == "revised-resp"
