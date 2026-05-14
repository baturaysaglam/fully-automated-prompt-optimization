# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from tenants.hotpotqa.code.retrieval import make_retrieval_node


class TestMakeRetrievalNode:
    """Tests for the BM25 retrieval module node factory."""

    def _make_state(self, step_outputs: dict[str, Any]) -> dict[str, Any]:
        return {"step_outputs": step_outputs}

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_retrieval_node_formats_passages(self, mock_search: Any) -> None:
        """Passages from BM25 are numbered with DSPy ChatAdapter format."""
        mock_search.return_value = [
            "Paris is the capital of France.",
            "France is in Western Europe.",
            "The Eiffel Tower is in Paris.",
        ]

        node = make_retrieval_node(
            query_key="query_hop1",
            data_dir="/tmp/bm25",
            k=3,
            output_key="retrieve_hop1",
        )
        state = self._make_state({"query_hop1": "capital of France"})
        result = node(state)

        assert "step_outputs" in result
        assert result["step_outputs"]["retrieve_hop1"] == (
            "[1] \u00abParis is the capital of France.\u00bb\n"
            "[2] \u00abFrance is in Western Europe.\u00bb\n"
            "[3] \u00abThe Eiffel Tower is in Paris.\u00bb"
        )
        mock_search.assert_called_once_with("capital of France", 3, "/tmp/bm25")

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_retrieval_node_finds_latest_query(self, mock_search: Any) -> None:
        """Node reads from the correct query_key in step_outputs."""
        mock_search.return_value = ["Result for hop 2."]

        node = make_retrieval_node(
            query_key="query_hop2",
            data_dir="/tmp/bm25",
            k=5,
            output_key="retrieve_hop2",
        )
        state = self._make_state({
            "query_hop1": "first hop query",
            "retrieve_hop1": "hop 1 passages",
            "summarize_hop1": "hop 1 summary",
            "query_hop2": "second hop query",
        })
        result = node(state)

        assert result["step_outputs"]["retrieve_hop2"] == "[1] \u00abResult for hop 2.\u00bb"
        mock_search.assert_called_once_with("second hop query", 5, "/tmp/bm25")

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_retrieval_node_preserves_existing_outputs(self, mock_search: Any) -> None:
        """Existing step_outputs are preserved when adding new retrieval output."""
        mock_search.return_value = ["Some passage."]

        node = make_retrieval_node(
            query_key="query_hop1",
            output_key="retrieve_hop1",
        )
        state = self._make_state({"query_hop1": "a query", "prior_step": "prior value"})
        result = node(state)

        assert result["step_outputs"]["prior_step"] == "prior value"
        assert result["step_outputs"]["retrieve_hop1"] == "[1] \u00abSome passage.\u00bb"

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_retrieval_node_default_data_dir_and_k(self, mock_search: Any) -> None:
        """Default data_dir and k are used when not specified."""
        mock_search.return_value = ["Passage."]

        node = make_retrieval_node(query_key="query_hop1", output_key="retrieve_hop1")
        state = self._make_state({"query_hop1": "test query"})
        node(state)

        mock_search.assert_called_once_with(
            "test query", 7, "tenants/hotpotqa/data/bm25"
        )

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_retrieval_node_reads_from_context_key(self, mock_search: Any) -> None:
        """When context_key is set, the query is read from state['context']."""
        mock_search.return_value = ["Context passage."]

        node = make_retrieval_node(
            output_key="retrieve_hop1",
            context_key="question",
        )
        state = {
            "context": {"question": "Who wrote Hamlet?"},
            "step_outputs": {},
        }
        result = node(state)

        mock_search.assert_called_once_with(
            "Who wrote Hamlet?", 7, "tenants/hotpotqa/data/bm25"
        )
        assert result["step_outputs"]["retrieve_hop1"] == "[1] \u00abContext passage.\u00bb"

    @patch("tenants.hotpotqa.code.retrieval._search_bm25")
    def test_retrieval_node_empty_passages(self, mock_search: Any) -> None:
        """Empty passage list produces empty string output."""
        mock_search.return_value = []

        node = make_retrieval_node(query_key="query_hop1", output_key="retrieve_hop1")
        state = self._make_state({"query_hop1": "obscure query"})
        result = node(state)

        assert result["step_outputs"]["retrieve_hop1"] == ""

    def test_rejects_both_query_key_and_context_key(self) -> None:
        """Passing both query_key and context_key raises ValueError."""
        with pytest.raises(ValueError, match="Exactly one"):
            make_retrieval_node(query_key="q", context_key="c")

    def test_rejects_neither_query_key_nor_context_key(self) -> None:
        """Passing neither query_key nor context_key raises ValueError."""
        with pytest.raises(ValueError, match="Exactly one"):
            make_retrieval_node()
