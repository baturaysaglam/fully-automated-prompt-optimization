# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""LiveBench Math scorer with task-specific scoring dispatch."""

from __future__ import annotations

import re
from typing import Any, Dict

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase
from tenants.livebench_math.code.scoring_utils.metric import calculate_livebench_score


def _strip_think_tags(text: str) -> str:
    """Remove <think>...</think> reasoning blocks from output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "question_d" not in case.expected:
            raise ValueError(f"Case {case.case_id} missing expected.question_d")
        qd = case.expected["question_d"]
        if "ground_truth" not in qd:
            raise ValueError(f"Case {case.case_id} missing expected.question_d.ground_truth")
        if "task" not in qd:
            raise ValueError(f"Case {case.case_id} missing expected.question_d.task")

    def score_case(
        self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        question_d = case.expected["question_d"]
        cleaned_output = _strip_think_tags(output_text)

        try:
            score, feedback = calculate_livebench_score(question_d, cleaned_output)
        except Exception as e:
            return {
                "composite_score": 0.0,
                "score_breakdown": {
                    "score": 0.0,
                },
                "metadata": {
                    "error": str(e),
                    "task": question_d.get("task", "unknown"),
                },
            }

        composite = score * 100.0

        return {
            "composite_score": composite,
            "score_breakdown": {
                "score": composite,
            },
            "metadata": {
                "task": question_d.get("task", ""),
                "subtask": question_d.get("subtask", ""),
                "feedback": feedback,
            },
        }
