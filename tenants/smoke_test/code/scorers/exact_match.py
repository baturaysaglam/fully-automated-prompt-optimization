# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Exact-match scorer for yes/no answers."""

from __future__ import annotations

from typing import Any, Dict

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "answer" not in case.expected:
            raise ValueError(f"Case {case.case_id} missing expected.answer")

    def score_case(self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]) -> Dict[str, Any]:
        expected = case.expected["answer"].strip().lower()
        actual = output_text.strip().lower()
        match = 100.0 if actual == expected else 0.0
        return {
            "composite_score": match,
            "score_breakdown": {"exact_match": match},
        }
