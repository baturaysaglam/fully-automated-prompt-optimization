# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the 8-node 3-hop retrieval chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from tenants.hover.chains.multi_hop import build_chain


class _StubProvider:
    def __init__(self, response: str = "stub response") -> None:
        self.response = response
        self.calls: List[List[Dict[str, str]]] = []

    def generate(self, messages: List[Dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.response


@pytest.fixture()
def prompt_dir(tmp_path: Path) -> Path:
    """Create minimal prompt templates for all 4 LLM modules."""
    modules = {
        "summarize1": "System: summarize\n\nUser: ${claim} ${steps.retrieve_hop1.output}",
        "query_hop2": "System: query\n\nUser: ${claim} ${steps.summarize_hop1.output}",
        "summarize2": "System: summarize\n\nUser: ${claim} ${steps.retrieve_hop2.output}",
        "query_hop3": "System: query\n\nUser: ${claim} ${steps.summarize_hop2.output}",
    }
    for name, content in modules.items():
        p = tmp_path / name / "variant-001.md"
        p.parent.mkdir(parents=True)
        p.write_text(content)
    return tmp_path


def _build_config(prompt_dir: Path) -> Dict[str, Any]:
    return {
        "prompt_paths": {
            "summarize1": str(prompt_dir / "summarize1" / "variant-001.md"),
            "query_hop2": str(prompt_dir / "query_hop2" / "variant-001.md"),
            "summarize2": str(prompt_dir / "summarize2" / "variant-001.md"),
            "query_hop3": str(prompt_dir / "query_hop3" / "variant-001.md"),
        },
        "retrieval_k": 7,
        "retrieval_k_hop3": 10,
        "bm25_data_dir": "tenants/hover/data/bm25",
    }


class TestBuildChain:
    def test_chain_compiles(self, prompt_dir: Path) -> None:
        provider = _StubProvider()
        chain = build_chain(provider, _build_config(prompt_dir))
        assert hasattr(chain, "invoke")

    def test_chain_has_8_nodes(self, prompt_dir: Path) -> None:
        """8 nodes: 3 retrieval + 4 LLM + 1 combine."""
        provider = _StubProvider()
        chain = build_chain(provider, _build_config(prompt_dir))
        graph = chain.get_graph()
        node_names = {n for n in graph.nodes if n not in ("__start__", "__end__")}
        expected = {
            "retrieve_hop1", "summarize_hop1",
            "query_hop2", "retrieve_hop2", "summarize_hop2",
            "query_hop3", "retrieve_hop3",
            "combine_retrievals",
        }
        assert node_names == expected

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_chain_invokes_with_mock(self, mock_search: Any, prompt_dir: Path) -> None:
        """Full chain execution with mocked provider and retrieval."""
        mock_search.return_value = ["passage A", "passage B"]
        provider = _StubProvider(response="mock output")
        chain = build_chain(provider, _build_config(prompt_dir))

        result = chain.invoke({
            "context": {"claim": "The Earth is round."},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        })

        # 4 LLM calls (summarize1, query_hop2, summarize2, query_hop3)
        assert len(provider.calls) == 4

        # 3 BM25 calls (retrieve_hop1, retrieve_hop2, retrieve_hop3)
        assert mock_search.call_count == 3

        # combine_retrievals sets output_text
        assert "retrieve_hop1" in result["output_text"]

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_retrieve_hop1_uses_claim(self, mock_search: Any, prompt_dir: Path) -> None:
        """First retrieval should use context['claim']."""
        mock_search.return_value = ["passage"]
        provider = _StubProvider(response="output")
        chain = build_chain(provider, _build_config(prompt_dir))

        chain.invoke({
            "context": {"claim": "Test claim here"},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        })

        first_call_query = mock_search.call_args_list[0][0][0]
        assert first_call_query == "Test claim here"
