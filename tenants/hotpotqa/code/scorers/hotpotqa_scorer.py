# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Optional

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase
from tenants.hotpotqa.code.scorers.normalize import normalize_answer


def compute_token_f1(predicted: str, expected: str) -> float:
    """Compute token-level F1 between already-normalized prediction and expected.

    Both *predicted* and *expected* must already be normalized via
    :func:`normalize_answer`.  Returns a score in [0, 100].
    """
    pred_tokens = predicted.split()
    exp_tokens = expected.split()

    if not pred_tokens and not exp_tokens:
        return 0.0
    if not pred_tokens or not exp_tokens:
        return 0.0

    common = sum((Counter(pred_tokens) & Counter(exp_tokens)).values())

    if common == 0:
        return 0.0

    precision = common / len(pred_tokens)
    recall = common / len(exp_tokens)
    f1 = 2 * precision * recall / (precision + recall)
    return round(f1 * 100, 2)


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "answer" not in case.expected:
            raise ValueError(f"Case '{case.case_id}' missing expected.answer")

    def score_case(self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]) -> Dict[str, Any]:
        predicted = normalize_answer(output_text)
        expected = normalize_answer(case.expected["answer"])

        em = 100.0 if predicted == expected else 0.0
        f1 = compute_token_f1(predicted, expected)

        return {
            # "composite_score" is a required key in the scoring contract;
            # for GEPA alignment we use pure EM (answer_exact_match).
            "composite_score": em,
            "score_breakdown": {"exact_match": em, "f1": f1},
        }

    def score_pipeline_case(
        self,
        case: EvalCase,
        step_outputs: Dict[str, str],
        scoring_profile: Dict[str, Any],
        output_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        if "answer" in step_outputs:
            final_output = step_outputs["answer"]
        elif output_text is not None:
            final_output = output_text
        elif step_outputs:
            final_output = list(step_outputs.values())[-1]
        else:
            raise ValueError("score_pipeline_case called with empty step_outputs and no output_text")
        return self.score_case(case, final_output, scoring_profile)
