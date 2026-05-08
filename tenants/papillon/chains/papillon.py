# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""3-node privacy-preserving chain mirroring GEPA's ``PAPILLON`` program.

Chain architecture (linear):
  craft_redacted_request → untrusted_llm → respond_to_query

Node roles (matching ``papillon_program.py:26``):
  - ``craft_redacted_request``: given the user query, produce a redacted
    request that can be safely sent to an untrusted LLM.
  - ``untrusted_llm``: the "untrusted" LLM responding to the redacted request.
    In the GEPA artifact this is a dedicated ``dspy.LM("openai/gpt-4.1-mini")``
    instance; here we reuse the shared FEPO provider, which uses the same
    model (same cost semantics, simpler plumbing). Noted in eval-operations.md.
  - ``respond_to_query``: compose the final response to the user, combining
    the untrusted LLM's answer with the original user query.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build the 3-node Papillon chain."""
    prompt_paths = {k: Path(v) for k, v in config["prompt_paths"].items()}
    graph = StateGraph(dict)

    graph.add_node(
        "craft_redacted_request",
        make_llm_node(provider, prompt_paths["craft_redacted_request"], output_key="craft_redacted_request"),
    )
    graph.add_node(
        "untrusted_llm",
        make_llm_node(provider, prompt_paths["untrusted_llm"], output_key="untrusted_llm"),
    )
    graph.add_node(
        "respond_to_query",
        make_llm_node(provider, prompt_paths["respond_to_query"], output_key="respond_to_query"),
    )

    graph.set_entry_point("craft_redacted_request")
    graph.add_edge("craft_redacted_request", "untrusted_llm")
    graph.add_edge("untrusted_llm", "respond_to_query")
    graph.add_edge("respond_to_query", END)
    return graph.compile()
