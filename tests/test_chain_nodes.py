# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for chain LLM node utilities: build_node_context and make_llm_node."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from src.hephaestus.chains.nodes import build_node_context, make_llm_node


class TestBuildNodeContext:
    def test_empty_state(self) -> None:
        """Returns empty dict for empty state."""
        result = build_node_context({})
        assert result == {}

    def test_with_case_context(self) -> None:
        """Includes case.context entries."""
        state: Dict[str, Any] = {"context": {"inputs.Name": "Alice", "inputs.Body": "hello"}}
        result = build_node_context(state)
        assert result == {"inputs.Name": "Alice", "inputs.Body": "hello"}

    def test_with_step_outputs(self) -> None:
        """Includes steps.<name>.output keys from step_outputs."""
        state: Dict[str, Any] = {
            "step_outputs": {"query_hop1": "answer_a", "classify": "label_b"},
        }
        result = build_node_context(state)
        assert result == {
            "steps.query_hop1.output": "answer_a",
            "steps.classify.output": "label_b",
        }

    def test_merges_both(self) -> None:
        """Merges case.context and step_outputs into one flat dict."""
        state: Dict[str, Any] = {
            "context": {"inputs.Name": "Alice"},
            "step_outputs": {"hop1": "result1"},
        }
        result = build_node_context(state)
        assert result == {
            "inputs.Name": "Alice",
            "steps.hop1.output": "result1",
        }


class TestMakeLlmNode:
    @staticmethod
    def _make_mock_provider(response: str = "mock_output") -> MagicMock:
        provider = MagicMock()
        provider.generate.return_value = response
        return provider

    def test_renders_and_calls_provider(self, tmp_path: Path) -> None:
        """Node renders the prompt template and calls provider.generate."""
        template = tmp_path / "template.md"
        template.write_text("System: sys\nUser: hello ${inputs.Name}", encoding="utf-8")

        provider = self._make_mock_provider("provider_reply")
        node = make_llm_node(provider, template)

        state: Dict[str, Any] = {
            "context": {"inputs.Name": "world"},
            "step_outputs": {},
        }
        _result = node(state)

        provider.generate.assert_called_once()
        call_messages = provider.generate.call_args[0][0]
        assert call_messages[0]["role"] == "system"
        assert call_messages[1]["content"] == "hello world"

    def test_updates_step_outputs(self, tmp_path: Path) -> None:
        """Node adds its output to step_outputs under output_key."""
        template = tmp_path / "template.md"
        template.write_text("User: hi", encoding="utf-8")

        provider = self._make_mock_provider("reply")
        node = make_llm_node(provider, template)

        result = node({"context": {}, "step_outputs": {}})
        assert result["step_outputs"]["output_text"] == "reply"

    def test_sets_output_text(self, tmp_path: Path) -> None:
        """Node sets output_text to the provider response."""
        template = tmp_path / "template.md"
        template.write_text("User: hi", encoding="utf-8")

        provider = self._make_mock_provider("the_answer")
        node = make_llm_node(provider, template)

        result = node({"context": {}, "step_outputs": {}})
        assert result["output_text"] == "the_answer"

    def test_custom_output_key(self, tmp_path: Path) -> None:
        """Custom output_key is used as the step_outputs key."""
        template = tmp_path / "template.md"
        template.write_text("User: hi", encoding="utf-8")

        provider = self._make_mock_provider("custom_reply")
        node = make_llm_node(provider, template, output_key="classify")

        result = node({"context": {}, "step_outputs": {}})
        assert "classify" in result["step_outputs"]
        assert result["step_outputs"]["classify"] == "custom_reply"
        assert result["output_text"] == "custom_reply"

    def test_preserves_existing_step_outputs(self, tmp_path: Path) -> None:
        """Node preserves prior step_outputs entries."""
        template = tmp_path / "template.md"
        template.write_text("User: prev=${steps.hop1.output}", encoding="utf-8")

        provider = self._make_mock_provider("hop2_result")
        node = make_llm_node(provider, template, output_key="hop2")

        state: Dict[str, Any] = {
            "context": {},
            "step_outputs": {"hop1": "hop1_result"},
        }
        result = node(state)
        assert result["step_outputs"]["hop1"] == "hop1_result"
        assert result["step_outputs"]["hop2"] == "hop2_result"

    def test_missing_placeholders_no_crash(self, tmp_path: Path) -> None:
        """Missing placeholders are replaced with empty string, no crash."""
        template = tmp_path / "template.md"
        template.write_text("User: hello ${inputs.Missing}", encoding="utf-8")

        provider = self._make_mock_provider("still_works")
        node = make_llm_node(provider, template)

        result = node({"context": {}, "step_outputs": {}})
        assert result["output_text"] == "still_works"
        provider.generate.assert_called_once()

    def test_template_read_at_build_time(self, tmp_path: Path) -> None:
        """Template is read once at build time, not at invoke time."""
        template = tmp_path / "template.md"
        template.write_text("User: original", encoding="utf-8")

        provider = self._make_mock_provider("reply")
        node = make_llm_node(provider, template)

        # Overwrite after build
        template.write_text("User: modified", encoding="utf-8")

        node({"context": {}, "step_outputs": {}})
        call_messages = provider.generate.call_args[0][0]
        assert "original" in call_messages[0]["content"]

    def test_make_llm_node_with_missing_template(self, tmp_path: Path) -> None:
        """FileNotFoundError raised when template path doesn't exist."""
        provider = self._make_mock_provider()
        bad_path = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            make_llm_node(provider, bad_path)
