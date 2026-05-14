# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Single-node answer chain for smoke_test tenant."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build a 1-node yes/no answer chain."""
    prompt_path = Path(config["prompt_paths"]["answer"])
    graph = StateGraph(dict)
    graph.add_node("answer", make_llm_node(provider, prompt_path))
    graph.set_entry_point("answer")
    graph.add_edge("answer", END)
    return graph.compile()
