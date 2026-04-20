# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from src.hephaestus.types import EvalCase

REQUIRED_KEYS = {"case_id", "task_type", "context", "expected", "metadata"}


def _validate_case(raw: dict, line_number: int) -> EvalCase:
    missing = REQUIRED_KEYS - set(raw)
    if missing:
        raise ValueError(
            f"Invalid dataset case at line {line_number}: missing keys {sorted(missing)}"
        )

    case_id = raw["case_id"]
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError(f"Invalid case_id at line {line_number}")

    context = raw["context"]
    if not isinstance(context, dict):
        raise ValueError(f"Invalid context at line {line_number}: expected object")

    expected = raw["expected"]
    if not isinstance(expected, dict):
        raise ValueError(f"Invalid expected at line {line_number}: expected object")

    metadata = raw["metadata"]
    if not isinstance(metadata, dict):
        raise ValueError(f"Invalid metadata at line {line_number}: expected object")

    messages_template = raw.get("messages_template")
    prompt_template_path = raw.get("prompt_template_path")
    if messages_template is not None and not isinstance(messages_template, dict):
        raise ValueError(f"Invalid messages_template at line {line_number}")
    if prompt_template_path is not None and not isinstance(prompt_template_path, str):
        raise ValueError(f"Invalid prompt_template_path at line {line_number}")

    return EvalCase(
        case_id=case_id,
        task_type=str(raw["task_type"]),
        context={str(k): str(v) for k, v in context.items()},
        expected=expected,
        metadata=metadata,
        messages_template=messages_template,
        prompt_template_path=prompt_template_path,
    )


def load_cases(path: Path) -> List[EvalCase]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset path not found: {path}")

    cases: List[EvalCase] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        raw = json.loads(text)
        cases.append(_validate_case(raw, index))
    return cases
