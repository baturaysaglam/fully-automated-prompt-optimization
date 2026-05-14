# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from src.hephaestus.engine.prompt_renderer import (
    build_case_prompt_with_context,
    render_prompt,
)


def test_render_prompt_replaces_placeholders_and_parses_messages():
    template = "System: sys\nUser: hello ${inputs.Name}\nAssistant: ignore"
    context = {"inputs.Name": "world"}

    result = render_prompt(template, context)

    assert result.prompt_messages == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello world"},
    ]
    assert result.diagnostics == []


def test_render_prompt_tracks_missing_context():
    template = "User: ${inputs.Missing}"
    result = render_prompt(template, context={})
    assert "inputs.Missing" in result.diagnostics


def test_render_prompt_does_not_truncate_inline_assistant_in_context():
    template = "System: sys\nUser: ${inputs.Body}\nAssistant: ignore"
    context = {"inputs.Body": "Quoted text Assistant: this stays"}

    result = render_prompt(template, context)

    assert result.prompt_messages == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "Quoted text Assistant: this stays"},
    ]


def test_render_prompt_does_not_truncate_multiline_assistant_in_context():
    template = "System: sys\nUser: ${inputs.Body}\nAssistant: ignore"
    context = {"inputs.Body": "First line\nAssistant: quoted line\nLast line"}

    result = render_prompt(template, context)

    assert result.prompt_messages == [
        {"role": "system", "content": "sys"},
        {
            "role": "user",
            "content": "First line\nAssistant: quoted line\nLast line",
        },
    ]


def test_render_prompt_excludes_assistant_section_but_tracks_diagnostics():
    template = "System: sys\nUser: hello\nAssistant: ${inputs.MissingInAssistant}"

    result = render_prompt(template, context={})

    assert result.prompt_messages == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello"},
    ]
    assert result.diagnostics == ["inputs.MissingInAssistant"]


def test_build_case_prompt_with_context_basic(tmp_path: Path) -> None:
    template = tmp_path / "template.md"
    template.write_text("System: sys\nUser: hello ${name}", encoding="utf-8")

    result = build_case_prompt_with_context({"name": "world"}, template)

    assert result.prompt_messages == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello world"},
    ]
    assert result.diagnostics == []


def test_build_case_prompt_with_context_dotted_keys(tmp_path: Path) -> None:
    template = tmp_path / "template.md"
    template.write_text(
        "System: sys\nUser: prior=${steps.foo.output} current=${steps.bar.output}",
        encoding="utf-8",
    )

    context = {
        "steps.foo.output": "answer_a",
        "steps.bar.output": "answer_b",
    }
    result = build_case_prompt_with_context(context, template)

    assert result.prompt_messages == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "prior=answer_a current=answer_b"},
    ]
    assert result.diagnostics == []
