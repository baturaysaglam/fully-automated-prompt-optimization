# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""2-node chain mirroring GEPA's ``IFBenchCoT2StageProgram``.

Chain architecture (linear):
  generate_response → ensure_correct_response

Matches ``ifbench_program.py:17–25``: the first node produces a draft
response to the user prompt; the second node revises the draft to ensure
it satisfies the instruction constraints.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build the 2-node IFBench chain."""
    prompt_paths = {k: Path(v) for k, v in config["prompt_paths"].items()}
    graph = StateGraph(dict)
    graph.add_node(
        "generate_response",
        make_llm_node(provider, prompt_paths["generate_response"], output_key="generate_response"),
    )
    graph.add_node(
        "ensure_correct_response",
        make_llm_node(
            provider, prompt_paths["ensure_correct_response"], output_key="ensure_correct_response"
        ),
    )
    graph.set_entry_point("generate_response")
    graph.add_edge("generate_response", "ensure_correct_response")
    graph.add_edge("ensure_correct_response", END)
    return graph.compile()
