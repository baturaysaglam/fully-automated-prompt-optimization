# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""AIME scorer matching GEPA's ``AIMEBench`` metric.

GEPA's metric (``gepa_artifact.benchmarks.AIME.__init__.metric``) does:

    correct = int(example['answer'])
    try: pred = int(prediction.answer)
    except ValueError: return 0
    return int(correct == pred)

We port that verbatim. The model is expected to produce an integer answer,
optionally wrapped in DSPy-style ``[[ ## answer ## ]]`` blocks; we extract
the integer with a robust regex. Score is a binary 0/100 for composite.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase

# Priority 1: final \boxed{N}. Priority 2: final [[ ## answer ## ]] block. Priority 3: last bare integer.
_BOXED_RE = re.compile(r"\\boxed\{\s*(-?\d+)\s*\}")
_DSPY_ANSWER_RE = re.compile(r"\[\[\s*##\s*answer\s*##\s*\]\]\s*(-?\d+)")
_INT_RE = re.compile(r"-?\d+")


def extract_integer_answer(text: str) -> Optional[int]:
    """Extract the model's integer answer from *text*.

    Tries, in order: last ``\\boxed{N}``, last DSPy ``[[ ## answer ## ]] N``,
    last bare integer in the text. Returns ``None`` if none are found.
    """
    boxed = _BOXED_RE.findall(text)
    if boxed:
        try:
            return int(boxed[-1])
        except ValueError:
            pass
    dspy = _DSPY_ANSWER_RE.findall(text)
    if dspy:
        try:
            return int(dspy[-1])
        except ValueError:
            pass
    ints = _INT_RE.findall(text)
    if ints:
        try:
            return int(ints[-1])
        except ValueError:
            pass
    return None


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "answer" not in case.expected:
            raise ValueError(f"Case '{case.case_id}' missing expected.answer")

    def score_case(
        self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            expected = int(str(case.expected["answer"]).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Case '{case.case_id}' has non-integer expected answer: {case.expected['answer']!r}"
            ) from exc

        predicted = extract_integer_answer(output_text)
        if predicted is None:
            return {
                "composite_score": 0.0,
                "score_breakdown": {"exact_match": 0.0, "parse_ok": 0.0},
            }
        em = 100.0 if predicted == expected else 0.0
        return {
            "composite_score": em,
            "score_breakdown": {"exact_match": em, "parse_ok": 100.0},
        }

    def score_pipeline_case(
        self,
        case: EvalCase,
        step_outputs: Dict[str, str],
        scoring_profile: Dict[str, Any],
        output_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        if "solve" in step_outputs:
            final = step_outputs["solve"]
        elif output_text is not None:
            final = output_text
        elif step_outputs:
            final = list(step_outputs.values())[-1]
        else:
            raise ValueError("score_pipeline_case called with empty step_outputs and no output_text")
        return self.score_case(case, final, scoring_profile)
