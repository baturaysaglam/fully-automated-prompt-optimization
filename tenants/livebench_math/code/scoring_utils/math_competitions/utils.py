# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0
#
# Adapted from LiveBench (https://github.com/LiveBench/LiveBench)
# Original code licensed under Apache-2.0.

"""AMC/SMC/AIME scoring utilities."""

from __future__ import annotations

import re
from typing import Tuple

from ..util import last_boxed_only_string, remove_boxed


def mathcontest_process_results_with_feedback(
    ground_truth: str, llm_answer: str, question_text: str, debug: bool = False
) -> Tuple[int, str]:
    """Score a multiple-choice math competition answer (AMC/SMC) with feedback."""
    score = 0
    feedback_details: list[str] = []
    parsed_answer = None

    if not (isinstance(ground_truth, str) and len(ground_truth) == 1 and "A" <= ground_truth <= "E"):
        raise ValueError("Ground truth must be a single capital letter between A and E.")

    # 1. <solution> tag check
    solution_matches = re.findall(r"<solution>(.*?)</solution>", llm_answer)
    if solution_matches:
        solution_match = solution_matches[-1]
        if len(set(solution_match)) == 1 and next(iter(set(solution_match))).lower() == ground_truth.lower():
            score = 1
            feedback_details.append(
                f"Correct answer '{solution_match}' found in <solution> tags."
            )
        else:
            feedback_details.append(
                f"Answer in <solution> tags ('{solution_match}') did not match ground truth ('{ground_truth}')."
            )
    else:
        feedback_details.append("No <solution> tags found.")

    # 2. 4x repeated letter
    if score == 0:
        if ground_truth * 4 in llm_answer:
            score = 1
            feedback_details.append(f"Correct answer detected as repeated letter pattern.")
        else:
            feedback_details.append("No repeated letter pattern detected.")

    # 3. Boxed answer
    if score == 0:
        llm_answer_boxed = llm_answer.replace("\\\\fbox{", "\\\\boxed{")
        last_boxed = last_boxed_only_string(llm_answer_boxed)
        if last_boxed:
            last_boxed_res = (
                remove_boxed(last_boxed)
                .replace("\\text{", "")
                .replace("}", "")
                .replace("\\", "")
                .lower()
            )
            if last_boxed_res in {"a", "b", "c", "d", "e"}:
                parsed_answer = last_boxed_res
                if parsed_answer == ground_truth.lower():
                    score = 1
                    feedback_details.append(f"Boxed answer matches ground truth.")
                else:
                    feedback_details.append(
                        f"Boxed answer '{last_boxed_res.upper()}' does not match '{ground_truth}'."
                    )
            else:
                feedback_details.append(f"Boxed content '{last_boxed_res}' is not a valid option (A-E).")
        else:
            feedback_details.append("No boxed answer found.")

    # 4. Explicit answer value at end
    if score == 0:
        value = _extract_answer_value(question_text, ground_truth)
        length_to_check = 20 + len(value)
        if value in llm_answer[-length_to_check:]:
            score = 1
            feedback_details.append(f"Found answer value '{value}' at end of output.")
        else:
            feedback_details.append(f"Did not find answer value at end of response.")

    # 5. Last line matching
    if score == 0:
        last_line = llm_answer.strip().split("\n")[-1]
        last_line_stripped = last_line.strip().replace("*", "").lower()
        if last_line_stripped == ground_truth.lower():
            score = 1
            feedback_details.append(f"Last line matches ground truth.")
        elif "(" in last_line and ")" in last_line:
            val = last_line.split("(")[1].split(")")[0]
            if val.lower() == ground_truth.lower():
                score = 1
                feedback_details.append(f"Last line parenthetical matches ground truth.")
            else:
                feedback_details.append(f"Last line parenthetical '{val}' does not match.")
        else:
            feedback_details.append(f"Last line does not match ground truth.")

    if score == 1:
        feedback_text = "Correct answer detected.\n" + "\n".join(feedback_details)
    else:
        feedback_text = (
            "Incorrect answer detected.\n"
            "Evaluation details:\n"
            + "\n".join(feedback_details)
            + "\n\nTips: Output your final answer as a single letter (A-E) in a "
            "<solution> tag, as a 5x repeated letter, or boxed in LaTeX."
        )

    return score, feedback_text


def aime_process_results(
    ground_truth: str, llm_answer: str, debug: bool = False
) -> Tuple[int, str]:
    """Score an AIME answer by checking if ground_truth appears in last 50 chars."""
    if ground_truth in llm_answer[-50:]:
        feedback_text = (
            f"Correct. Ground truth '{ground_truth}' found in the last 50 characters."
        )
        return 1, feedback_text

    feedback_text = (
        f"Incorrect. Ground truth '{ground_truth}' not found in the last 50 characters. "
        "The correct answer must appear within the final 50 characters of your response."
    )
    return 0, feedback_text


def _extract_answer_value(statement: str, letter: str) -> str:
    """Extract the answer value for a given letter from AMC-style question text."""
    pattern = r"\\textbf{\(([A-E])\)\s?}(.*?)(?:\\qquad|\$)"
    matches = re.findall(pattern, statement)
    answers = {match[0]: match[1].strip() for match in matches}
    answer = answers.get(letter, None)

    if not answer or answer == "":
        answer = "FAILURE"

    answer = answer.strip().strip("$").strip("~")
    return answer
