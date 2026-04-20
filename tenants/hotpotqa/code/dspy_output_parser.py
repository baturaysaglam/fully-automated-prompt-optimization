# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Parse DSPy-formatted structured output to extract a named field.

DSPy's ChatAdapter produces output in ``[[ ## field_name ## ]]`` format::

    [[ ## reasoning ## ]]
    Let's think step by step ...

    [[ ## answer ## ]]
    Albus Dumbledore

    [[ ## completed ## ]]

This module extracts the content of a specific field from that structured
output.  If the output does not contain DSPy markers, it is returned as-is
so the parser is safe to use with any prompt variant.
"""

from __future__ import annotations

import re
from typing import Callable

FIELD_PATTERN = re.compile(r"\[\[\s*##\s*(\w+)\s*##\s*\]\]")


def extract_dspy_field(text: str, field_name: str) -> str:
    """Extract the content of *field_name* from DSPy-structured output.

    Returns the raw text if no DSPy markers are found (safe for non-DSPy prompts).
    """
    markers = list(FIELD_PATTERN.finditer(text))
    if not markers:
        return text.strip()

    for i, m in enumerate(markers):
        if m.group(1) == field_name:
            start = m.end()
            end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            return text[start:end].strip()

    # Field not found — return raw text
    return text.strip()


def make_dspy_field_parser(field_name: str) -> Callable[[str], str]:
    """Return a parser callable that extracts *field_name* from DSPy output."""
    def parser(text: str) -> str:
        return extract_dspy_field(text, field_name)
    return parser
