# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""6-node multi-hop QA chain aligned with the GEPA paper (arXiv:2507.19457).

Chain architecture (linear):
  retrieve_hop1 → summarize_hop1 → query_hop2 → retrieve_hop2 → summarize_hop2 → answer

Nodes:
  - 4 LLM nodes using 4 prompt templates
    (summarize1, summarize2, generate_query_with_context, generate_answer)
  - 2 BM25 retrieval nodes

This matches GEPA's HoVerMultiHop program where the first hop uses the raw
question as the retrieval query (no query-generation LLM call) and the final
hop is replaced by answer generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.chains.types import ChainState
from src.hephaestus.providers.base import ProviderClient
from tenants.hotpotqa.code.dspy_output_parser import make_dspy_field_parser
from tenants.hotpotqa.code.retrieval import make_retrieval_node

# Map each LLM node to the DSPy output field it should extract.
# The parser is a no-op when the output lacks DSPy markers, so this is safe
# for both DSPy-format (baseline) and hand-written (variant-001+) prompts.
_OUTPUT_FIELD_MAP = {
    "summarize1": "summary",
    "generate_query_with_context": "query",
    "summarize2": "summary",
    "generate_answer": "answer",
}


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build a 6-node multi-hop QA chain aligned with GEPA's HoVerMultiHop."""
    prompt_paths = {k: Path(v) for k, v in config["prompt_paths"].items()}
    data_dir = config.get("bm25_data_dir", "tenants/hotpotqa/data/bm25")
    retrieval_k = config.get("retrieval_k", 7)

    graph = StateGraph(ChainState)

    # Hop 1: retrieve using raw question from context, then summarize
    graph.add_node(
        "retrieve_hop1",
        make_retrieval_node(
            data_dir=data_dir,
            k=retrieval_k,
            output_key="retrieve_hop1",
            context_key="question",
        ),
    )
    graph.add_node(
        "summarize_hop1",
        make_llm_node(
            provider, prompt_paths["summarize1"], output_key="summarize_hop1",
            output_parser=make_dspy_field_parser(_OUTPUT_FIELD_MAP["summarize1"]),
        ),
    )

    # Hop 2: generate follow-up query, retrieve, then summarize
    graph.add_node(
        "query_hop2",
        make_llm_node(
            provider, prompt_paths["generate_query_with_context"], output_key="query_hop2",
            output_parser=make_dspy_field_parser(_OUTPUT_FIELD_MAP["generate_query_with_context"]),
        ),
    )
    graph.add_node(
        "retrieve_hop2",
        make_retrieval_node("query_hop2", data_dir, retrieval_k, output_key="retrieve_hop2"),
    )
    graph.add_node(
        "summarize_hop2",
        make_llm_node(
            provider, prompt_paths["summarize2"], output_key="summarize_hop2",
            output_parser=make_dspy_field_parser(_OUTPUT_FIELD_MAP["summarize2"]),
        ),
    )

    # Answer
    graph.add_node(
        "answer",
        make_llm_node(
            provider, prompt_paths["generate_answer"], output_key="answer",
            output_parser=make_dspy_field_parser(_OUTPUT_FIELD_MAP["generate_answer"]),
        ),
    )

    # Linear edges
    graph.set_entry_point("retrieve_hop1")
    graph.add_edge("retrieve_hop1", "summarize_hop1")
    graph.add_edge("summarize_hop1", "query_hop2")
    graph.add_edge("query_hop2", "retrieve_hop2")
    graph.add_edge("retrieve_hop2", "summarize_hop2")
    graph.add_edge("summarize_hop2", "answer")
    graph.add_edge("answer", END)

    return graph.compile()
