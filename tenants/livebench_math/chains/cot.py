# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Single-node CoT math solver for the livebench_math tenant.

Mirrors GEPA's ``gepa_artifact.benchmarks.livebench_math.livebenchmath_program.program_cot``
— a one-stage ChainOfThought for ``question -> answer``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build a 1-node chain-of-thought solver reading ``${question}``."""
    prompt_path = Path(config["prompt_paths"]["solve"])
    graph = StateGraph(dict)
    graph.add_node("solve", make_llm_node(provider, prompt_path, output_key="solve"))
    graph.set_entry_point("solve")
    graph.add_edge("solve", END)
    return graph.compile()
