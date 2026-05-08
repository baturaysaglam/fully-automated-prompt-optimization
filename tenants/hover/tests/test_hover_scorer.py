# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the hover tenant scorer."""

from __future__ import annotations

import pytest

from src.hephaestus.types import EvalCase
from tenants.hover.code.scorers.hover_scorer import Scorer, _parse_passage_titles


def _make_case(titles: list[str]) -> EvalCase:
    return EvalCase(
        case_id="hover-test-0",
        task_type="claim_verification_retrieval",
        context={"claim": "A claim."},
        expected={
            "supporting_facts": [{"key": t, "value": 0} for t in titles],
            "label": "SUPPORTED",
            "label_raw": 0,
        },
        metadata={"source": "hover"},
    )


def _passages(titles_and_bodies: list[tuple[str, str]]) -> str:
    """Format passages the way make_retrieval_node does: '[i] «title | body»'."""
    parts = []
    for i, (title, body) in enumerate(titles_and_bodies, 1):
        parts.append(f"[{i}] «{title} | {body}»")
    return "\n".join(parts)


@pytest.fixture()
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture()
def scoring_profile() -> dict[str, object]:
    return {}


# --- validate_case ---


def test_validate_case_valid(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case(["Alice", "Bob", "Charlie"])
    scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_supporting_facts(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = EvalCase(
        case_id="bad",
        task_type="claim_verification_retrieval",
        context={"claim": "x"},
        expected={"label": "SUPPORTED", "label_raw": 0},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.supporting_facts"):
        scorer.validate_case(case, scoring_profile)


def test_validate_case_empty_supporting_facts(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case([])
    with pytest.raises(ValueError, match="empty or non-list supporting_facts"):
        scorer.validate_case(case, scoring_profile)


# --- _parse_passage_titles ---


def test_parse_passage_titles_basic() -> None:
    text = _passages([("Alice Smith", "a bio"), ("Bob Jones", "another bio")])
    assert _parse_passage_titles(text) == ["Alice Smith", "Bob Jones"]


def test_parse_passage_titles_empty() -> None:
    assert _parse_passage_titles("") == []


# --- score_pipeline_case: full-subset subset check ---


def test_pipeline_subset_success(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case(["Alice", "Bob", "Charlie"])
    step_outputs = {
        "retrieve_hop1": _passages([("Alice", "bio")]),
        "retrieve_hop2": _passages([("Bob", "bio")]),
        "retrieve_hop3": _passages([("Charlie", "bio"), ("Dave", "distractor")]),
    }
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 100.0
    assert result["score_breakdown"]["retrieval_subset"] == 100.0
    assert result["score_breakdown"]["title_recall"] == 100.0


def test_pipeline_subset_missing_title(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case(["Alice", "Bob", "Charlie"])
    step_outputs = {
        "retrieve_hop1": _passages([("Alice", "bio")]),
        "retrieve_hop2": _passages([("Bob", "bio")]),
        "retrieve_hop3": _passages([("Dave", "distractor")]),
    }
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 0.0  # Charlie missing
    assert result["score_breakdown"]["retrieval_subset"] == 0.0
    assert result["score_breakdown"]["gold_titles_found"] == 2.0
    assert result["score_breakdown"]["gold_titles_total"] == 3.0


def test_pipeline_subset_normalization(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """Title matching uses normalize_answer (lowercase, punctuation-stripped)."""
    case = _make_case(["Alice Smith", "Bob Jones", "Charlie Brown"])
    step_outputs = {
        "retrieve_hop1": _passages([("alice smith", "bio")]),  # case-differ
        "retrieve_hop2": _passages([("Bob Jones", "bio")]),
        "retrieve_hop3": _passages([("Charlie Brown.", "bio")]),  # punct-differ
    }
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 100.0
