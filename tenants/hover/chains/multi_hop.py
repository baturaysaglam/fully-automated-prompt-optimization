# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""8-node 3-hop claim verification chain for HoVer.

Chain architecture (linear):
  retrieve_hop1 → summarize_hop1 → query_hop2 → retrieve_hop2 →
  summarize_hop2 → query_hop3 → retrieve_hop3 → combine_retrievals

Nodes:
  - 4 LLM nodes (summarize1, query_hop2, summarize2, query_hop3)
  - 3 BM25 retrieval nodes (hops 1-2 use k=7, hop 3 uses k=10)
  - 1 combine node (joins all 3 retrieval outputs into output_text)

Reuses the BM25 retrieval module from hotpotqa.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient
from tenants.hotpotqa.code.retrieval import make_retrieval_node


def _combine_retrievals(state: Dict[str, Any]) -> Dict[str, Any]:
    """Join all 3 retrieval outputs into output_text."""
    step_outputs = dict(state.get("step_outputs", {}))
    parts = []
    for key in ("retrieve_hop1", "retrieve_hop2", "retrieve_hop3"):
        if key in step_outputs:
            parts.append(f"--- {key} ---\n{step_outputs[key]}")
    output_text = "\n\n".join(parts)
    return {"output_text": output_text}


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build a 3-hop retrieval chain for claim verification."""
    prompt_paths = {k: Path(v) for k, v in config["prompt_paths"].items()}
    data_dir = config.get("bm25_data_dir", "tenants/hover/data/bm25")
    retrieval_k = config.get("retrieval_k", 7)
    retrieval_k_hop3 = config.get("retrieval_k_hop3", 10)

    graph = StateGraph(dict)

    # Hop 1: retrieve using claim from context
    graph.add_node(
        "retrieve_hop1",
        make_retrieval_node(
            data_dir=data_dir,
            k=retrieval_k,
            output_key="retrieve_hop1",
            context_key="claim",
        ),
    )
    graph.add_node(
        "summarize_hop1",
        make_llm_node(provider, prompt_paths["summarize1"], output_key="summarize_hop1"),
    )

    # Hop 2: generate query, retrieve, summarize
    graph.add_node(
        "query_hop2",
        make_llm_node(provider, prompt_paths["query_hop2"], output_key="query_hop2"),
    )
    graph.add_node(
        "retrieve_hop2",
        make_retrieval_node("query_hop2", data_dir, retrieval_k, output_key="retrieve_hop2"),
    )
    graph.add_node(
        "summarize_hop2",
        make_llm_node(provider, prompt_paths["summarize2"], output_key="summarize_hop2"),
    )

    # Hop 3: generate query, retrieve
    graph.add_node(
        "query_hop3",
        make_llm_node(provider, prompt_paths["query_hop3"], output_key="query_hop3"),
    )
    graph.add_node(
        "retrieve_hop3",
        make_retrieval_node("query_hop3", data_dir, retrieval_k_hop3, output_key="retrieve_hop3"),
    )

    # Combine all retrieval outputs
    graph.add_node("combine_retrievals", _combine_retrievals)

    # Linear edges
    graph.set_entry_point("retrieve_hop1")
    graph.add_edge("retrieve_hop1", "summarize_hop1")
    graph.add_edge("summarize_hop1", "query_hop2")
    graph.add_edge("query_hop2", "retrieve_hop2")
    graph.add_edge("retrieve_hop2", "summarize_hop2")
    graph.add_edge("summarize_hop2", "query_hop3")
    graph.add_edge("query_hop3", "retrieve_hop3")
    graph.add_edge("retrieve_hop3", "combine_retrievals")
    graph.add_edge("combine_retrievals", END)

    return graph.compile()
