# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""AIME scorer with exact match and LLM-based answer equivalence.

Scoring follows the methodology from ETGPO (arxiv 2602.00997):
1. Extract an integer answer from the model output.
2. If it exactly matches the expected answer, score 100.
3. If not, optionally call an LLM judge to check equivalence.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase


def extract_answer(text: str) -> Optional[str]:
    r"""Extract the integer answer from model output.

    Priority:
    1. Last \boxed{N} pattern
    2. Last standalone integer in the text
    """
    # Look for \boxed{...} — take the last one
    boxed = re.findall(r"\\boxed\{(\d+)\}", text)
    if boxed:
        return boxed[-1]

    # Fall back to last standalone integer
    integers = re.findall(r"\b(\d+)\b", text)
    if integers:
        return integers[-1]

    return None


def _build_judge_prompt(problem: str, expected: str, predicted: str) -> str:
    return (
        "You are a math competition answer checker. "
        "Determine whether the predicted answer is equivalent to the expected answer.\n\n"
        f"Problem: {problem}\n"
        f"Expected answer: {expected}\n"
        f"Predicted answer: {predicted}\n\n"
        "Are these answers equivalent? Reply with only YES or NO."
    )


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "answer" not in case.expected:
            raise ValueError(f"Case {case.case_id} missing expected.answer")

    def score_case(
        self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        expected = str(case.expected["answer"]).strip()
        predicted = extract_answer(output_text)

        # Exact match
        if predicted is not None and predicted == expected:
            return {
                "composite_score": 100.0,
                "score_breakdown": {"exact_match": 100.0, "llm_equiv": 100.0},
            }

        # LLM equivalence check (if configured)
        tenant_config = scoring_profile.get("tenant_config", {})
        judge_model = tenant_config.get("judge_model")
        if judge_model and predicted is not None:
            try:
                llm_match = self._llm_equiv_check(
                    case, expected, predicted, judge_model, tenant_config
                )
                if llm_match:
                    return {
                        "composite_score": 100.0,
                        "score_breakdown": {"exact_match": 0.0, "llm_equiv": 100.0},
                    }
            except Exception:
                pass  # Fall through to failure score

        return {
            "composite_score": 0.0,
            "score_breakdown": {
                "exact_match": 0.0,
                "llm_equiv": 0.0,
                "predicted_answer": float(predicted) if predicted else 0.0,
            },
        }

    def _llm_equiv_check(
        self,
        case: EvalCase,
        expected: str,
        predicted: str,
        judge_model: str,
        tenant_config: Dict[str, Any],
    ) -> bool:
        from src.hephaestus.providers import build_provider_client

        provider = build_provider_client(
            tenant_config.get("judge_provider", "openai"),
            {"model": judge_model, "temperature": 0.0, "max_tokens": 8},
        )
        problem = case.context.get("problem", "")
        prompt = _build_judge_prompt(problem, expected, predicted)
        response = provider.generate(
            [{"role": "system", "content": prompt}]
        )
        return response.strip().upper().startswith("YES")
