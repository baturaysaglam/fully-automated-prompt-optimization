# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Single-node math solving chain for aime2025 tenant."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build a 1-node chain-of-thought math solving chain."""
    prompt_path = Path(config["prompt_paths"]["solve"])
    graph = StateGraph(dict)
    graph.add_node("solve", make_llm_node(provider, prompt_path))
    graph.set_entry_point("solve")
    graph.add_edge("solve", END)
    return graph.compile()
