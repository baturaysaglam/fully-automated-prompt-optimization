# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the papillon 3-node chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from tenants.papillon.chains.papillon import build_chain


class _StubProvider:
    def __init__(self, responses: List[str] | None = None) -> None:
        self.responses = responses or ["redacted", "untrusted-answer", "final"]
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
        "craft_redacted_request": "System: redact\n\nUser: ${user_query}",
        "untrusted_llm": "System: untrusted\n\nUser: ${steps.craft_redacted_request.output}",
        "respond_to_query": (
            "System: respond\n\nUser: ${user_query} "
            "${steps.craft_redacted_request.output} ${steps.untrusted_llm.output}"
        ),
    }
    for name, content in modules.items():
        p = tmp_path / name / "variant-001.md"
        p.parent.mkdir(parents=True)
        p.write_text(content, encoding="utf-8")
    return tmp_path


def _build_config(prompt_dir: Path) -> Dict[str, Any]:
    return {
        "prompt_paths": {
            "craft_redacted_request": str(prompt_dir / "craft_redacted_request" / "variant-001.md"),
            "untrusted_llm": str(prompt_dir / "untrusted_llm" / "variant-001.md"),
            "respond_to_query": str(prompt_dir / "respond_to_query" / "variant-001.md"),
        }
    }


def test_chain_compiles(prompt_dir: Path) -> None:
    chain = build_chain(_StubProvider(), _build_config(prompt_dir))
    assert hasattr(chain, "invoke")


def test_chain_has_3_nodes(prompt_dir: Path) -> None:
    chain = build_chain(_StubProvider(), _build_config(prompt_dir))
    node_names = {n for n in chain.get_graph().nodes if n not in ("__start__", "__end__")}
    assert node_names == {"craft_redacted_request", "untrusted_llm", "respond_to_query"}


def test_chain_three_provider_calls_in_order(prompt_dir: Path) -> None:
    provider = _StubProvider(responses=["redacted-1", "untrusted-2", "final-3"])
    chain = build_chain(provider, _build_config(prompt_dir))
    result = chain.invoke(
        {
            "context": {"user_query": "My phone is 555-0100."},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        }
    )
    assert len(provider.calls) == 3
    assert result["step_outputs"]["craft_redacted_request"] == "redacted-1"
    assert result["step_outputs"]["untrusted_llm"] == "untrusted-2"
    assert result["step_outputs"]["respond_to_query"] == "final-3"
