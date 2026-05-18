# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0
#
# Adapted from LiveBench (https://github.com/LiveBench/LiveBench)
# Original code licensed under Apache-2.0.

"""IMO/USAMO proof rearrangement scoring utilities."""

from __future__ import annotations

from typing import Tuple

from ..util import last_boxed_only_string, remove_boxed


def proof_rearrangement_process_results(
    ground_truth: str, llm_answer: str, edit_distance: bool = False, debug: bool = False
) -> Tuple[float, str]:
    """Score an olympiad proof rearrangement answer."""
    ground_truth_list = [int(n) for n in ground_truth.split(",")]

    completions = _extract_expression_completions(llm_answer, debug)

    if edit_distance:
        from Levenshtein import distance

        dist = distance(completions, ground_truth_list)
        frac_matches = 1 - (dist / max(len(completions), len(ground_truth_list)))
        feedback_text = (
            f"Score: {frac_matches * 100:.2f}%. "
            f"Parsed answer: '{completions}', ground truth: '{ground_truth_list}'. "
            "Scoring uses edit distance."
        )
    else:
        match = [
            (completions[i] == ground_truth_list[i]) if i < len(ground_truth_list) else 0
            for i in range(len(completions))
        ]
        frac_matches = sum(match) / len(match) if match else 0
        feedback_text = (
            f"Score: {frac_matches * 100:.2f}%. "
            f"Parsed answer: '{completions}', ground truth: '{ground_truth_list}'. "
            "Scoring uses positional matching."
        )

    return frac_matches, feedback_text


def _remove_nonnumeric_chars_at_ends(s: str) -> Tuple[str, int]:
    """Strip non-digit characters from both ends, return cleaned string and removed count."""
    start_index = 0
    while start_index < len(s) and not s[start_index].isdigit():
        start_index += 1
    end_index = start_index
    while end_index < len(s) and s[end_index].isdigit():
        end_index += 1
    return s[start_index:end_index], len(s) - (end_index - start_index)


def _extract_expression_completions(generation: str, debug: bool) -> list:
    """Extract a list of integers from an olympiad-style generation."""
    numbers = None

    # Strategy 1: look for "answer:" followed by comma-separated numbers
    if "answer:" in generation.lower():
        lines = generation.lower().strip().split("\n")
        answer_line = None
        answer_index = None
        for i, line in enumerate(lines):
            if "answer:" in line:
                answer_line = line
                answer_index = i
        answer_str = (
            answer_line.split("answer:")[1]
            .replace("answer:", "")
            .replace("**", "")
            .replace(".", "")
            .strip()
        )
        if answer_str == "" and answer_index < len(lines) - 1:
            answer_str = (
                lines[answer_index + 1]
                .replace("answer:", "")
                .replace("**", "")
                .replace(".", "")
                .strip()
            )
        numbers = []
        for n in answer_str.split(","):
            n = (
                n.strip()
                .split(" ")[-1]
                .replace("$", "")
                .replace("{", "")
                .replace("}", "")
                .replace("\\", "")
                .replace("boxed", "")
                .replace("<", "")
                .replace(">", "")
            )
            try:
                numbers.append(int(n))
            except ValueError:
                numbers.append("NO ANSWER")
        if not numbers or set(numbers) == {"NO ANSWER"}:
            numbers = None

    # Strategy 2: extract from \boxed{...}
    if numbers is None and "\\boxed" in generation:
        boxed = last_boxed_only_string(generation)
        if boxed is not None:
            string = remove_boxed(boxed)
        else:
            string = generation
        string = string.replace("\\text{", "").replace("}", "").replace("\\", "")
        numbers = []
        for n in string.strip().split(","):
            try:
                numbers.append(int(n.strip()))
            except ValueError:
                numbers.append("NO ANSWER")
        if not numbers or set(numbers) == {"NO ANSWER"}:
            numbers = None

    # Strategy 3: last line
    if numbers is None:
        last_line = generation.strip().lower().split("\n")[-1]
        numbers = []
        for n in last_line.strip().split(","):
            n, _ = _remove_nonnumeric_chars_at_ends(n)
            if not n.strip():
                continue
            try:
                numbers.append(int(n.strip()))
            except ValueError:
                numbers.append("NO ANSWER")
        if not numbers or set(numbers) == {"NO ANSWER"}:
            numbers = None

    # Strategy 4: fallback — split on "answer:" and parse
    if numbers is None:
        split_string = "answer:"
        parts = [k.strip() for k in generation.lower().split(split_string)[-1].split(",")]
        new_numbers = []
        for i, n in enumerate(parts):
            n, num_removed = _remove_nonnumeric_chars_at_ends(n)
            if n != "" and n != "₂":
                try:
                    new_numbers.append(int(n))
                except ValueError:
                    pass
            if i > 0 and num_removed > 0:
                break
        numbers = new_numbers

    return numbers
