# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0
#
# Adapted from LiveBench (https://github.com/LiveBench/LiveBench)
# Original code licensed under Apache-2.0.

"""LaTeX box extraction utilities."""

from __future__ import annotations

from typing import Optional


def last_boxed_only_string(string: str) -> Optional[str]:
    """Find the last \\boxed{...} or \\fbox{...} in a string."""
    if "\\boxed " in string:
        return "\\boxed " + string.split("\\boxed ")[-1].split("$")[0]

    idx = string.rfind("\\boxed")
    if idx < 0:
        idx = string.rfind("\\fbox")
        if idx < 0:
            return None

    i = idx
    right_brace_idx = None
    num_left_braces_open = 0
    while i < len(string):
        if string[i] == "{":
            num_left_braces_open += 1
        if string[i] == "}":
            num_left_braces_open -= 1
            if num_left_braces_open == 0:
                right_brace_idx = i
                break
        i += 1

    if right_brace_idx is None:
        return None

    return string[idx:right_brace_idx + 1].replace("$", "").replace("fbox", "boxed")


def remove_boxed(s: str) -> str:
    """Strip the \\boxed{} wrapper and return the inner content."""
    if "\\boxed " in s:
        left = "\\boxed "
        assert s[:len(left)] == left
        return s[len(left):]

    left = "\\boxed{"
    assert s[:len(left)] == left
    assert s[-1] == "}"
    return s[len(left):-1]
