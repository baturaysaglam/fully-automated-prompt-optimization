# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""HoVer scorer — binary retrieval recall.

Scoring: all gold supporting titles must be found among retrieved passage
titles. If all are found → 100, otherwise → 0.
"""

from __future__ import annotations

import re
import string
from typing import Any, Dict

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase


def normalize_title(title: str) -> str:
    """Normalize a title for comparison: lowercase, strip articles/punctuation/whitespace."""
    text = title.lower()
    # Remove articles
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Collapse whitespace
    text = " ".join(text.split())
    return text


def _extract_titles_from_passages(output_text: str) -> set[str]:
    """Extract titles from BM25 retrieval output format.

    Retrieval output format: [N] «Title | passage text»
    """
    titles = set()
    for line in output_text.split("\n"):
        line = line.strip()
        # Match [N] «Title | ...»
        m = re.match(r"\[\d+\]\s*[«\"](.+?)\s*\|", line)
        if m:
            titles.add(normalize_title(m.group(1)))
    return titles


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "supporting_titles" not in case.expected:
            raise ValueError(f"Case {case.case_id} missing expected.supporting_titles")

    def score_case(
        self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        gold_titles = {normalize_title(t) for t in case.expected["supporting_titles"]}
        retrieved_titles = _extract_titles_from_passages(output_text)

        found = gold_titles & retrieved_titles
        all_found = gold_titles <= retrieved_titles

        composite = 100.0 if all_found else 0.0
        num_gold = len(gold_titles)
        num_found = len(found)
        partial_recall = (num_found / num_gold * 100.0) if num_gold > 0 else 0.0

        return {
            "composite_score": composite,
            "score_breakdown": {
                "recall": composite,
                "partial_recall": partial_recall,
                "num_gold": float(num_gold),
                "num_found": float(num_found),
                "num_missing": float(num_gold - num_found),
            },
        }
