# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""CTI-CWE scorer using faith's SequentialMatcher for CWE ID extraction."""
from __future__ import annotations

from typing import Any, Dict

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase


def _build_matcher():
    from faith._internal.algo.matching import SequentialMatcher
    from faith._internal.io.benchmarks import benchmarks_root
    from faith.benchmark.config import load_config_from_path

    config = load_config_from_path(benchmarks_root() / "ctibench-rcm")
    answer_formats = config["output_processing"]["answer_formats"]
    return SequentialMatcher(*answer_formats)


class Scorer(BaseScorer):
    def __init__(self):
        self._matcher = _build_matcher()

    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "cwe_id" not in case.expected:
            raise ValueError(f"Case '{case.case_id}' missing expected.cwe_id")

    # Numeric encoding of answer_format for score_breakdown (must be 0-100).
    _FORMAT_SCORES = {"proper": 100.0, "improper": 50.0, "invalid": 0.0}

    def score_case(self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]) -> Dict[str, Any]:
        extracted, answer_format = self._matcher(output_text)
        fmt = str(answer_format)

        expected = case.expected["cwe_id"]
        exact_match = 100.0 if extracted == expected else 0.0
        format_score = self._FORMAT_SCORES.get(fmt, 0.0)

        return {
            "composite_score": exact_match,
            "score_breakdown": {
                "exact_match": exact_match,
                "answer_format": format_score,
            },
            "answer_format_label": fmt,
        }
