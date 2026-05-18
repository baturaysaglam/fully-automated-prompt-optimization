# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""3-step privacy-preserving chain: redact → call untrusted → reconstruct.

The chain redacts PII from the query, sends the redacted query to an
untrusted LLM, then reconstructs the response using the original context.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.hephaestus.chains.nodes import make_llm_node
from src.hephaestus.providers.base import ProviderClient


def _make_untrusted_node(config: Dict[str, Any]) -> Any:
    """Create a node that calls an untrusted LLM with the redacted query."""
    untrusted_config = config.get("untrusted_model", {})

    def node(state: Dict[str, Any]) -> Dict[str, Any]:
        from src.hephaestus.providers import build_provider_client

        step_outputs = dict(state.get("step_outputs", {}))
        redacted_query = step_outputs.get("redact_query", "")

        provider = build_provider_client(
            untrusted_config.get("provider", "openai"),
            {
                "model": untrusted_config.get("model", "gpt-4.1-mini"),
                "temperature": untrusted_config.get("temperature", 1.0),
                "max_tokens": untrusted_config.get("max_tokens", 4096),
            },
        )

        response = provider.generate(
            [{"role": "user", "content": redacted_query}]
        )

        step_outputs["untrusted_response"] = response
        return {"step_outputs": step_outputs}

    return node


def build_chain(provider: ProviderClient, config: Dict[str, Any]) -> Any:
    """Build a 3-step privacy-preserving chain."""
    prompt_paths = {k: Path(v) for k, v in config["prompt_paths"].items()}

    graph = StateGraph(dict)

    # Step 1: Redact PII from the query
    graph.add_node(
        "redact_query",
        make_llm_node(provider, prompt_paths["redact_query"], output_key="redact_query"),
    )

    # Step 2: Call untrusted LLM with redacted query
    graph.add_node("call_untrusted", _make_untrusted_node(config))

    # Step 3: Reconstruct response using original context + untrusted response
    graph.add_node(
        "reconstruct_response",
        make_llm_node(provider, prompt_paths["reconstruct_response"], output_key="reconstruct_response"),
    )

    # Linear edges
    graph.set_entry_point("redact_query")
    graph.add_edge("redact_query", "call_untrusted")
    graph.add_edge("call_untrusted", "reconstruct_response")
    graph.add_edge("reconstruct_response", END)

    return graph.compile()
