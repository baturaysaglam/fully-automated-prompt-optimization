# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Two-node instruction following chain: generate → verify."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build a 2-node chain: generate response, then verify/rewrite."""
    generate_path = Path(config["prompt_paths"]["generate"])
    verify_path = Path(config["prompt_paths"]["verify"])

    graph = StateGraph(dict)
    graph.add_node("generate", make_llm_node(provider, generate_path, output_key="generate"))
    graph.add_node("verify", make_llm_node(provider, verify_path, output_key="verify"))

    graph.set_entry_point("generate")
    graph.add_edge("generate", "verify")
    graph.add_edge("verify", END)
    return graph.compile()
