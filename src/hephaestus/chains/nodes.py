# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Node factories that produce callables compatible with LangGraph's StateGraph.add_node()."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List

from src.hephaestus.engine.prompt_renderer import render_prompt
from src.hephaestus.providers.base import ProviderClient


def build_node_context(state: Dict[str, Any]) -> Dict[str, str]:
    """Build a flat context dict from chain state for prompt rendering.

    Merges case.context with prior step outputs (keyed as steps.<name>.output).
    """
    context: Dict[str, str] = {}
    if "context" in state:
        context.update(state["context"])
    for k, v in state.get("step_outputs", {}).items():
        context[f"steps.{k}.output"] = str(v)
    return context


def make_llm_node(
    provider: ProviderClient,
    prompt_template_path: Path,
    output_key: str = "output_text",
    output_parser: Callable[[str], str] | None = None,
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Return a callable(state) -> state_update suitable for StateGraph.add_node().

    The returned function:
    1. Builds context from state (case.context + prior step outputs)
    2. Renders the prompt template with that context
    3. Calls provider.generate()
    4. Optionally applies *output_parser* to the raw LLM output
    5. Returns state updates: output_text, step_outputs[output_key]

    LangGraph nodes are plain callables — there is no built-in LLM node
    abstraction, so this factory fills that gap for our eval chains.

    The template is read once at build time for efficiency.
    """
    template_text = prompt_template_path.read_text(encoding="utf-8")

    def node(state: Dict[str, Any]) -> Dict[str, Any]:
        context = build_node_context(state)
        render_result = render_prompt(template_text, context)
        output = provider.generate(render_result.prompt_messages)
        if output_parser is not None:
            output = output_parser(output)

        step_outputs = dict(state.get("step_outputs", {}))
        step_outputs[output_key] = output

        diags: List[str] = list(state.get("diagnostics", []))
        diags.extend(render_result.diagnostics)

        return {
            "output_text": output,
            "step_outputs": step_outputs,
            "diagnostics": diags,
        }

    return node
