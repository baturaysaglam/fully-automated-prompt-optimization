# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""HoVer scorer mirroring GEPA's ``discrete_retrieval_eval`` metric.

GEPA's metric (``gepa_artifact/benchmarks/hover/hover_utils.py:8``) checks
whether the set of normalized gold supporting-fact titles is a subset of the
set of normalized titles found in the retrieved passages (across all hops).
We port that verbatim; composite is 0 or 100.

Retrieved passages are formatted as ``"{title} | {text}"`` (see
``tenants/hotpotqa/code/retrieval.py``); we split on ``" | "`` to extract titles.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase
from tenants.hotpotqa.code.scorers.normalize import normalize_answer

# Passages are written by make_retrieval_node as:
#   "[1] «{title} | {text}»\n[2] «...»\n..."
_PASSAGE_RE = re.compile(r"\[\d+\]\s*\xab(.+?)\xbb", re.DOTALL)


def _parse_passage_titles(passages_text: str) -> List[str]:
    """Extract the ``title`` portion (before the first ' | ') from each passage."""
    titles: List[str] = []
    for match in _PASSAGE_RE.findall(passages_text):
        # Each match is "title | text"; take everything before the first " | ".
        head = match.split(" | ", 1)[0]
        titles.append(head)
    return titles


def _gold_titles(supporting_facts: Iterable[Dict[str, Any]]) -> List[str]:
    return [str(fact["key"]) for fact in supporting_facts]


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "supporting_facts" not in case.expected:
            raise ValueError(f"Case '{case.case_id}' missing expected.supporting_facts")
        sf = case.expected["supporting_facts"]
        if not isinstance(sf, list) or not sf:
            raise ValueError(f"Case '{case.case_id}' has empty or non-list supporting_facts")

    def score_case(
        self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        # When there are no step_outputs, score_case is called directly; the scorer
        # degrades to comparing titles discovered in `output_text` alone.
        gold = {normalize_answer(t) for t in _gold_titles(case.expected["supporting_facts"])}
        found = {normalize_answer(t) for t in _parse_passage_titles(output_text)}
        return self._score_from_title_sets(gold, found)

    def score_pipeline_case(
        self,
        case: EvalCase,
        step_outputs: Dict[str, str],
        scoring_profile: Dict[str, Any],
        output_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Concatenate passages from all three retrieval hops, matching GEPA's
        # ``retrieved_docs = hop1_docs + hop2_docs + hop3_docs``.
        pooled: List[str] = []
        for key in ("retrieve_hop1", "retrieve_hop2", "retrieve_hop3"):
            chunk = step_outputs.get(key)
            if chunk:
                pooled.extend(_parse_passage_titles(chunk))
        gold = {normalize_answer(t) for t in _gold_titles(case.expected["supporting_facts"])}
        found = {normalize_answer(t) for t in pooled}
        return self._score_from_title_sets(gold, found)

    @staticmethod
    def _score_from_title_sets(gold: set, found: set) -> Dict[str, Any]:
        subset = gold.issubset(found) if gold else True
        composite = 100.0 if subset else 0.0
        overlap = len(gold & found)
        recall = 100.0 * overlap / len(gold) if gold else 100.0
        return {
            "composite_score": composite,
            "score_breakdown": {
                "retrieval_subset": composite,
                "gold_titles_found": float(overlap),
                "gold_titles_total": float(len(gold)),
                "title_recall": recall,
            },
        }
