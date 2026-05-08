# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the aime tenant 1-node CoT chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from tenants.aime.chains.cot import build_chain


class _StubProvider:
    def __init__(self, response: str = r"\boxed{42}") -> None:
        self.response = response
        self.calls: List[List[Dict[str, str]]] = []

    def generate(self, messages: List[Dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.response


@pytest.fixture()
def prompt_dir(tmp_path: Path) -> Path:
    prompt_file = tmp_path / "solve" / "variant-001.md"
    prompt_file.parent.mkdir(parents=True)
    prompt_file.write_text("System: solve\n\nUser: ${problem}", encoding="utf-8")
    return tmp_path


def _build_config(prompt_dir: Path) -> Dict[str, Any]:
    return {"prompt_paths": {"solve": str(prompt_dir / "solve" / "variant-001.md")}}


def test_chain_compiles(prompt_dir: Path) -> None:
    provider = _StubProvider()
    chain = build_chain(provider, _build_config(prompt_dir))
    assert hasattr(chain, "invoke")


def test_chain_has_single_node(prompt_dir: Path) -> None:
    provider = _StubProvider()
    chain = build_chain(provider, _build_config(prompt_dir))
    node_names = {n for n in chain.get_graph().nodes if n not in ("__start__", "__end__")}
    assert node_names == {"solve"}


def test_chain_invokes_provider_once(prompt_dir: Path) -> None:
    provider = _StubProvider(response=r"\boxed{42}")
    chain = build_chain(provider, _build_config(prompt_dir))
    result = chain.invoke(
        {
            "context": {"problem": "What is 2+2?"},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        }
    )
    assert len(provider.calls) == 1
    assert result["step_outputs"]["solve"] == r"\boxed{42}"
    assert result["output_text"] == r"\boxed{42}"
