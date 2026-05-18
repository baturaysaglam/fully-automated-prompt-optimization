# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the 3-step privacy chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from tenants.papillon.chains.privacy_chain import build_chain


class _StubProvider:
    def __init__(self, response: str = "stub response") -> None:
        self.response = response
        self.calls: List[List[Dict[str, str]]] = []

    def generate(self, messages: List[Dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.response


@pytest.fixture()
def prompt_dir(tmp_path: Path) -> Path:
    redact = tmp_path / "redact_query" / "variant-001.md"
    redact.parent.mkdir(parents=True)
    redact.write_text("System: Redact PII\n\nUser: ${query}")

    recon = tmp_path / "reconstruct_response" / "variant-001.md"
    recon.parent.mkdir(parents=True)
    recon.write_text(
        "System: Reconstruct\n\n"
        "User: ${query} ${steps.untrusted_response.output}"
    )
    return tmp_path


def _build_config(prompt_dir: Path) -> Dict[str, Any]:
    return {
        "prompt_paths": {
            "redact_query": str(prompt_dir / "redact_query" / "variant-001.md"),
            "reconstruct_response": str(prompt_dir / "reconstruct_response" / "variant-001.md"),
        },
        "untrusted_model": {
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "temperature": 1.0,
            "max_tokens": 4096,
        },
    }


class TestBuildChain:
    def test_chain_compiles(self, prompt_dir: Path) -> None:
        provider = _StubProvider()
        chain = build_chain(provider, _build_config(prompt_dir))
        assert hasattr(chain, "invoke")

    def test_chain_has_3_nodes(self, prompt_dir: Path) -> None:
        provider = _StubProvider()
        chain = build_chain(provider, _build_config(prompt_dir))
        graph = chain.get_graph()
        node_names = {n for n in graph.nodes if n not in ("__start__", "__end__")}
        assert node_names == {"redact_query", "call_untrusted", "reconstruct_response"}

    @patch("src.hephaestus.providers.build_provider_client")
    def test_chain_execution(self, mock_build_provider, prompt_dir: Path) -> None:
        """Full chain execution with mocked untrusted provider."""
        mock_untrusted = _StubProvider(response="untrusted response")
        mock_build_provider.return_value = mock_untrusted

        responses = iter(["redacted query", "final response"])
        provider = _StubProvider()
        provider.generate = lambda msgs: next(responses)

        chain = build_chain(provider, _build_config(prompt_dir))

        result = chain.invoke({
            "context": {"query": "Help John Smith at 123 Main St"},
            "step_outputs": {},
            "output_text": "",
            "diagnostics": [],
        })

        assert mock_build_provider.called
        assert result["step_outputs"]["redact_query"] == "redacted query"
        assert result["step_outputs"]["untrusted_response"] == "untrusted response"
        assert result["output_text"] == "final response"
