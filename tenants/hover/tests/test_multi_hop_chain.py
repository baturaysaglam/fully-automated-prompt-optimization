# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the hover tenant 7-node multi-hop retrieval chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from tenants.hover.chains.multi_hop import build_chain


class _StubProvider:
    def __init__(self, response: str = "stub output") -> None:
        self.response = response
        self.calls: List[List[Dict[str, str]]] = []

    def generate(self, messages: List[Dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.response


@pytest.fixture()
def prompt_dir(tmp_path: Path) -> Path:
    for name in ("summarize1", "summarize2", "create_query_hop2", "create_query_hop3"):
        p = tmp_path / name / "variant-001.md"
        p.parent.mkdir(parents=True)
        p.write_text(f"System: {name}\n\nUser: ${{claim}}", encoding="utf-8")
    return tmp_path


def _build_config(prompt_dir: Path) -> Dict[str, Any]:
    return {
        "prompt_paths": {
            "summarize1": str(prompt_dir / "summarize1" / "variant-001.md"),
            "summarize2": str(prompt_dir / "summarize2" / "variant-001.md"),
            "create_query_hop2": str(prompt_dir / "create_query_hop2" / "variant-001.md"),
            "create_query_hop3": str(prompt_dir / "create_query_hop3" / "variant-001.md"),
        },
        "retrieval_k_hop1": 7,
        "retrieval_k_hop2": 7,
        "retrieval_k_hop3": 10,
        "bm25_data_dir": "tenants/hotpotqa/data/bm25",
    }


def test_chain_compiles(prompt_dir: Path) -> None:
    chain = build_chain(_StubProvider(), _build_config(prompt_dir))
    assert hasattr(chain, "invoke")


def test_chain_has_7_nodes(prompt_dir: Path) -> None:
    chain = build_chain(_StubProvider(), _build_config(prompt_dir))
    node_names = {n for n in chain.get_graph().nodes if n not in ("__start__", "__end__")}
    assert node_names == {
        "retrieve_hop1",
        "summarize_hop1",
        "query_hop2",
        "retrieve_hop2",
        "summarize_hop2",
        "query_hop3",
        "retrieve_hop3",
    }


@patch("tenants.hotpotqa.code.retrieval._search_bm25")
def test_chain_invokes_4_llm_calls(mock_search: Any, prompt_dir: Path) -> None:
    mock_search.return_value = ["Alice | bio"]
    provider = _StubProvider(response="follow-up query")
    chain = build_chain(provider, _build_config(prompt_dir))
    result = chain.invoke(
        {
            "context": {"claim": "Alice knows Bob."},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        }
    )
    # 4 LLM nodes: summarize_hop1, query_hop2, summarize_hop2, query_hop3.
    assert len(provider.calls) == 4
    # All three retrieval steps populated.
    for key in ("retrieve_hop1", "retrieve_hop2", "retrieve_hop3"):
        assert key in result["step_outputs"]


@patch("tenants.hotpotqa.code.retrieval._search_bm25")
def test_retrieve_hop1_uses_raw_claim(mock_search: Any, prompt_dir: Path) -> None:
    mock_search.return_value = ["Alice | bio"]
    chain = build_chain(_StubProvider(), _build_config(prompt_dir))
    chain.invoke(
        {
            "context": {"claim": "Alice knows Bob."},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        }
    )
    first_query = mock_search.call_args_list[0][0][0]
    assert first_query == "Alice knows Bob."
