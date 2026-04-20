# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.hephaestus.types import PromptRenderResult

ASSISTANT_SECTION_PATTERN = re.compile(r"(?m)^[ \t]*Assistant:")


def _extract_block(text: str, start_marker: str, end_marker: Optional[str]) -> Optional[str]:
    start = text.find(start_marker)
    if start == -1:
        return None
    start += len(start_marker)
    end = text.find(end_marker, start) if end_marker else -1
    if end_marker and end != -1:
        return text[start:end].strip()
    return text[start:].strip()


def _find_assistant_section_start(template_text: str) -> Optional[int]:
    match = ASSISTANT_SECTION_PATTERN.search(template_text)
    if not match:
        return None
    return match.start()


def _replace_placeholders(text: str, context: Dict[str, str]) -> Tuple[str, List[str]]:
    rendered = text
    diagnostics: List[str] = []

    while True:
        start = rendered.find("${")
        if start == -1:
            break
        end = rendered.find("}", start)
        if end == -1:
            break

        placeholder = rendered[start + 2 : end]
        replacement = context.get(placeholder, "")
        if replacement == "":
            diagnostics.append(placeholder)
        rendered = rendered[:start] + replacement + rendered[end + 1 :]

    return rendered, diagnostics


def _build_messages_from_template(text: str) -> Optional[List[Dict[str, str]]]:
    system_block = _extract_block(text, "System:", "User:")
    user_block = _extract_block(text, "User:", None)
    if system_block is None or user_block is None:
        return None
    return [
        {"role": "system", "content": system_block},
        {"role": "user", "content": user_block},
    ]


def render_prompt(template_text: str, context: Dict[str, str]) -> PromptRenderResult:
    assistant_start = _find_assistant_section_start(template_text)
    if assistant_start is None:
        prompt_template = template_text
        ignored_template = ""
    else:
        prompt_template = template_text[:assistant_start]
        ignored_template = template_text[assistant_start:]

    rendered_prompt, missing_prompt = _replace_placeholders(prompt_template, context)
    _, missing_ignored = _replace_placeholders(ignored_template, context)
    text = rendered_prompt.rstrip()

    messages = _build_messages_from_template(text)
    if messages is None:
        messages = [{"role": "user", "content": text}]
        prompt_text = text
    else:
        prompt_text = f"{messages[0]['content']}\n\n{messages[1]['content']}"

    return PromptRenderResult(
        prompt_text=prompt_text,
        prompt_messages=messages,
        diagnostics=sorted(set(missing_prompt + missing_ignored)),
    )


def build_case_prompt_with_context(
    context: Dict[str, str], template_path: Path
) -> PromptRenderResult:
    """Render a prompt template with an explicit context dict.

    Used by chain LLM nodes where context includes prior step outputs.
    """
    template_text = template_path.read_text(encoding="utf-8")
    return render_prompt(template_text, context)
