# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0
#
# Adapted from LiveBench (https://github.com/LiveBench/LiveBench)
# Original code licensed under Apache-2.0.

"""LiveBench Math scoring dispatcher."""

from __future__ import annotations

import re
from typing import Tuple

from .math_competitions.utils import (
    aime_process_results,
    mathcontest_process_results_with_feedback,
)
from .olympiad.utils import proof_rearrangement_process_results
from .AMPS_Hard.utils import amps_hard_process_results


def calculate_livebench_score(
    question_d: dict, llm_answer: str, debug: bool = False
) -> Tuple[float, str]:
    """Route scoring to the appropriate task-specific scorer.

    Returns (score, feedback_text) where score is 0-1.
    """
    question = question_d
    ground_truth = question.get("ground_truth", None)

    if ground_truth is None:
        raise ValueError("Question must have 'ground_truth' field.")

    task = question["task"]
    task_or_subtask = question.get("subtask", question["task"])

    # Strip <think>...</think> reasoning tags
    llm_answer = re.sub(r"<think>.*?</think>", "", llm_answer, flags=re.DOTALL)

    question_text = question["turns"][0]
    splits = task_or_subtask.split("_")

    try:
        if len(splits) > 0 and (
            splits[0] in ["amc", "smc", "aime", "imo", "usamo"]
            or (len(splits) > 1 and splits[1] == "amc")
        ):
            if splits[0] in ["amc", "smc"] or (len(splits) > 1 and splits[1] == "amc"):
                score, feedback = mathcontest_process_results_with_feedback(
                    ground_truth, llm_answer, question_text, debug
                )
            elif splits[0] == "aime":
                score, feedback = aime_process_results(ground_truth, llm_answer, debug)
            elif splits[0] in ["imo", "usamo"]:
                score, feedback = proof_rearrangement_process_results(
                    ground_truth, llm_answer, edit_distance=True, debug=debug
                )
            else:
                raise ValueError(
                    f"Invalid task/subtask: {task}, {task_or_subtask}"
                )
        elif "amps_hard" in task_or_subtask:
            score, feedback = amps_hard_process_results(ground_truth, llm_answer, debug)
        else:
            raise NotImplementedError(
                f"Task '{task_or_subtask}' has not been implemented."
            )
    except Exception as e:
        raise RuntimeError(
            f"Error evaluating question {question.get('question_id', 'unknown')}"
        ) from e

    return score, feedback
