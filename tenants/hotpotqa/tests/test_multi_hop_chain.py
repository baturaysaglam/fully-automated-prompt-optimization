# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the 6-node multi-hop QA chain (GEPA-aligned)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from tenants.hotpotqa.chains.multi_hop import build_chain


class _StubProvider:
    """Minimal ProviderClient stub that returns a canned response."""

    def __init__(self, response: str = "stub response") -> None:
        self.response = response
        self.calls: List[List[Dict[str, str]]] = []

    def generate(self, messages: List[Dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.response


@pytest.fixture()
def prompt_dir(tmp_path: Path) -> Path:
    """Create minimal prompt templates in a temp dir matching the 3 GEPA modules + answer."""
    modules = {
        "generate_query_with_context": (
            "System: query with context\n\n"
            "User: ${question} ${steps.summarize_hop1.output}"
        ),
        "summarize1": (
            "System: summarize hop 1\n\n"
            "User: ${question} ${steps.retrieve_hop1.output}"
        ),
        "summarize2": (
            "System: summarize hop 2\n\n"
            "User: ${question} ${steps.summarize_hop1.output} "
            "${steps.retrieve_hop2.output}"
        ),
        "generate_answer": (
            "System: answer\n\n"
            "User: ${question} ${steps.summarize_hop1.output} "
            "${steps.summarize_hop2.output}"
        ),
    }
    for name, content in modules.items():
        p = tmp_path / name / "variant-001.md"
        p.parent.mkdir(parents=True)
        p.write_text(content)
    return tmp_path


def _build_config(prompt_dir: Path) -> Dict[str, Any]:
    return {
        "prompt_paths": {
            "generate_query_with_context": str(
                prompt_dir / "generate_query_with_context" / "variant-001.md"
            ),
            "summarize1": str(prompt_dir / "summarize1" / "variant-001.md"),
            "summarize2": str(prompt_dir / "summarize2" / "variant-001.md"),
            "generate_answer": str(prompt_dir / "generate_answer" / "variant-001.md"),
        },
        "retrieval_k": 7,
        "bm25_data_dir": "tenants/hotpotqa/data/bm25",
    }


class TestBuildChain:
    """Tests for the build_chain factory function."""

    def test_chain_compiles(self, prompt_dir: Path) -> None:
        """build_chain returns a compiled graph (has invoke method)."""
        provider = _StubProvider()
        config = _build_config(prompt_dir)
        chain = build_chain(provider, config)
        assert hasattr(chain, "invoke")

    def test_chain_has_6_nodes(self, prompt_dir: Path) -> None:
        """The compiled chain contains exactly 6 nodes (excluding __start__ / __end__)."""
        provider = _StubProvider()
        config = _build_config(prompt_dir)
        chain = build_chain(provider, config)

        graph = chain.get_graph()
        node_names = {
            n for n in graph.nodes if n not in ("__start__", "__end__")
        }
        assert len(node_names) == 6
        expected = {
            "retrieve_hop1",
            "summarize_hop1",
            "query_hop2",
            "retrieve_hop2",
            "summarize_hop2",
            "answer",
        }
        assert node_names == expected

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_chain_invokes_with_mock_provider(
        self, mock_search: Any, prompt_dir: Path
    ) -> None:
        """Full chain execution with mocked provider and retrieval completes."""
        mock_search.return_value = ["passage A", "passage B"]
        provider = _StubProvider(response="mock output")
        config = _build_config(prompt_dir)
        chain = build_chain(provider, config)

        result = chain.invoke({
            "context": {"question": "Who wrote Hamlet?"},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        })

        # Provider should be called 4 times (3 LLM nodes + 1 answer node)
        assert len(provider.calls) == 4

        # Final output_text is from the last LLM node
        assert result["output_text"] == "mock output"

        # step_outputs should contain all expected keys
        so = result["step_outputs"]
        for key in [
            "retrieve_hop1",
            "summarize_hop1",
            "query_hop2",
            "retrieve_hop2",
            "summarize_hop2",
            "answer",
        ]:
            assert key in so

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_retrieve_hop1_reads_from_context(
        self, mock_search: Any, prompt_dir: Path
    ) -> None:
        """retrieve_hop1 reads the query from context['question'], not step_outputs."""
        mock_search.return_value = ["passage about Hamlet"]
        provider = _StubProvider(response="mock output")
        config = _build_config(prompt_dir)
        chain = build_chain(provider, config)

        _result = chain.invoke({
            "context": {"question": "Who wrote Hamlet?"},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        })

        # First BM25 call should use the raw question
        first_call_query = mock_search.call_args_list[0][0][0]
        assert first_call_query == "Who wrote Hamlet?"
