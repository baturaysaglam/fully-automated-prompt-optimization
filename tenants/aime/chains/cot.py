# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Single-node chain-of-thought math solver for the aime tenant.

Mirrors the GEPA artifact's ``gepa_artifact.benchmarks.AIME.AIME_program.program_cot``
which is a one-stage ``ChainOfThought("problem -> answer")`` module. We
expose it as a LangGraph ``StateGraph(dict)`` with a single ``solve`` node.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build a 1-node chain-of-thought math solver. Reads ``${problem}``."""
    prompt_path = Path(config["prompt_paths"]["solve"])
    graph = StateGraph(dict)
    graph.add_node("solve", make_llm_node(provider, prompt_path, output_key="solve"))
    graph.set_entry_point("solve")
    graph.add_edge("solve", END)
    return graph.compile()
