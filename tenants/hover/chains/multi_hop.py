# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""7-node claim-retrieval chain mirroring GEPA's ``HoverMultiHop``.

Chain architecture (linear):
  retrieve_hop1 → summarize_hop1 → query_hop2 → retrieve_hop2 →
  summarize_hop2 → query_hop3 → retrieve_hop3

- Hop 1 retrieves using the raw claim (no query-gen LLM call).
- Hops 2 and 3 generate a query via ChainOfThought-style LLM prompt, then retrieve.
- Retrieval uses BM25 over the shared ``wiki.abstracts.2017`` corpus at
  ``tenants/hotpotqa/data/bm25`` (same corpus as the GEPA artifact).
- Final ``retrieved_docs`` = concatenation of passages from all three hops,
  exposed to the scorer via ``step_outputs``.

Matches GEPA's ``hover_program.py:313–333`` verbatim in structure and k-values
(k=7 for hops 1 and 2, k=10 for hop 3).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient
from tenants.hotpotqa.code.retrieval import make_retrieval_node


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build GEPA's 7-node HoverMultiHop chain."""
    prompt_paths = {k: Path(v) for k, v in config["prompt_paths"].items()}
    data_dir = config.get("bm25_data_dir", "tenants/hotpotqa/data/bm25")
    k_hop1 = config.get("retrieval_k_hop1", 7)
    k_hop2 = config.get("retrieval_k_hop2", 7)
    k_hop3 = config.get("retrieval_k_hop3", 10)

    graph = StateGraph(dict)

    # Hop 1: retrieve using the raw claim as the query, then summarize
    graph.add_node(
        "retrieve_hop1",
        make_retrieval_node(
            data_dir=data_dir,
            k=k_hop1,
            output_key="retrieve_hop1",
            context_key="claim",
        ),
    )
    graph.add_node(
        "summarize_hop1",
        make_llm_node(provider, prompt_paths["summarize1"], output_key="summarize_hop1"),
    )

    # Hop 2: generate follow-up query, retrieve, then summarize
    graph.add_node(
        "query_hop2",
        make_llm_node(provider, prompt_paths["create_query_hop2"], output_key="query_hop2"),
    )
    graph.add_node(
        "retrieve_hop2",
        make_retrieval_node(query_key="query_hop2", data_dir=data_dir, k=k_hop2, output_key="retrieve_hop2"),
    )
    graph.add_node(
        "summarize_hop2",
        make_llm_node(provider, prompt_paths["summarize2"], output_key="summarize_hop2"),
    )

    # Hop 3: generate follow-up query, retrieve (k=10), no final summarize
    graph.add_node(
        "query_hop3",
        make_llm_node(provider, prompt_paths["create_query_hop3"], output_key="query_hop3"),
    )
    graph.add_node(
        "retrieve_hop3",
        make_retrieval_node(query_key="query_hop3", data_dir=data_dir, k=k_hop3, output_key="retrieve_hop3"),
    )

    graph.set_entry_point("retrieve_hop1")
    graph.add_edge("retrieve_hop1", "summarize_hop1")
    graph.add_edge("summarize_hop1", "query_hop2")
    graph.add_edge("query_hop2", "retrieve_hop2")
    graph.add_edge("retrieve_hop2", "summarize_hop2")
    graph.add_edge("summarize_hop2", "query_hop3")
    graph.add_edge("query_hop3", "retrieve_hop3")
    graph.add_edge("retrieve_hop3", END)

    return graph.compile()
