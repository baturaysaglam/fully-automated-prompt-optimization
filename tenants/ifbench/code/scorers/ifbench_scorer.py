# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""IFBench scorer — instruction adherence fraction."""

from __future__ import annotations

import logging
from typing import Any, Dict

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase

logger = logging.getLogger(__name__)


def _ensure_nltk():
    """Lazily download NLTK punkt tokenizer on first use."""
    import nltk
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)


def _check_instructions(response: str, instruction_id_list: list, kwargs_list: list, prompt: str) -> tuple[float, str]:
    """Check how many instructions the response follows.

    Uses 8 response variants (original, remove first/last line, both,
    and each with '*' stripped) — a constraint passes if ANY variant satisfies it.

    Returns (fraction_followed, feedback_text).
    """
    _ensure_nltk()

    from tenants.ifbench.code.scoring_utils import instructions_registry

    r = response.split("\n")
    response_remove_first = "\n".join(r[1:]).strip()
    response_remove_last = "\n".join(r[:-1]).strip()
    response_remove_both = "\n".join(r[1:-1]).strip()
    revised_response = response.replace("*", "")
    revised_response_remove_first = response_remove_first.replace("*", "")
    revised_response_remove_last = response_remove_last.replace("*", "")
    revised_response_remove_both = response_remove_both.replace("*", "")

    all_responses = [
        response,
        revised_response,
        response_remove_first,
        response_remove_last,
        response_remove_both,
        revised_response_remove_first,
        revised_response_remove_last,
        revised_response_remove_both,
    ]

    is_following_list = []
    correct_feedbacks = []
    incorrect_feedbacks = []

    for index, instruction_id in enumerate(instruction_id_list):
        if instruction_id not in instructions_registry.INSTRUCTION_DICT:
            logger.warning("Unknown instruction ID: %s", instruction_id)
            is_following_list.append(False)
            incorrect_feedbacks.append(f"Unknown instruction: {instruction_id}")
            continue

        instruction_cls = instructions_registry.INSTRUCTION_DICT[instruction_id]
        instruction = instruction_cls(instruction_id)

        kw = {k: v for k, v in kwargs_list[index].items() if v is not None}

        ins_text = instruction.build_description(**kw)
        args = instruction.get_instruction_args()
        if args and "prompt" in args:
            ins_text = instruction.build_description(prompt=prompt)

        is_following = False
        for resp_variant in all_responses:
            if resp_variant.strip() and instruction.check_following(resp_variant):
                is_following = True
                break

        if is_following:
            correct_feedbacks.append(ins_text)
        else:
            incorrect_feedbacks.append(ins_text)

        is_following_list.append(is_following)

    if not is_following_list:
        return 0.0, "No instructions to check."

    fraction = sum(is_following_list) / len(is_following_list)

    feedback_parts = []
    if correct_feedbacks:
        feedback_parts.append(
            "Correctly followed:\n" + "\n".join(f"  - {f}" for f in correct_feedbacks)
        )
    if incorrect_feedbacks:
        feedback_parts.append(
            "Did not follow:\n" + "\n".join(f"  - {f}" for f in incorrect_feedbacks)
        )

    return fraction, "\n".join(feedback_parts)


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "instruction_id_list" not in case.expected:
            raise ValueError(f"Case {case.case_id} missing expected.instruction_id_list")
        if "kwargs" not in case.expected:
            raise ValueError(f"Case {case.case_id} missing expected.kwargs")

    def score_case(
        self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        instruction_id_list = case.expected["instruction_id_list"]
        kwargs_list = case.expected["kwargs"]
        prompt = case.context.get("prompt", "")

        fraction, feedback = _check_instructions(
            output_text, instruction_id_list, kwargs_list, prompt
        )

        composite = fraction * 100.0

        return {
            "composite_score": composite,
            "score_breakdown": {
                "instruction_adherence": composite,
                "instructions_total": len(instruction_id_list),
                "instructions_followed": int(fraction * len(instruction_id_list)),
            },
            "metadata": {
                "feedback": feedback,
            },
        }
