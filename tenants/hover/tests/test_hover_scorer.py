# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the HoVer scorer."""

from __future__ import annotations

import pytest

from src.hephaestus.types import EvalCase
from tenants.hover.code.scorers.hover_scorer import Scorer, normalize_title


def _make_case(supporting_titles: list[str], case_id: str = "test-001") -> EvalCase:
    return EvalCase(
        case_id=case_id,
        task_type="claim_verification",
        context={"claim": "Test claim"},
        expected={"supporting_titles": supporting_titles, "label": "SUPPORTED"},
        metadata={"source": "hover", "num_hops": 3},
    )


@pytest.fixture()
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture()
def scoring_profile() -> dict:
    return {}


def test_normalize_title_basic() -> None:
    assert normalize_title("The Dog") == "dog"
    assert normalize_title("A Cat") == "cat"
    assert normalize_title("Hello, World!") == "hello world"


def test_all_titles_found(scorer: Scorer, scoring_profile: dict) -> None:
    """All gold titles in retrieval → 100."""
    case = _make_case(["Alpha", "Beta"])
    output = (
        '[1] «Alpha | some passage text»\n'
        '[2] «Beta | another passage»\n'
        '[3] «Gamma | irrelevant»'
    )
    result = scorer.score_case(case, output, scoring_profile)
    assert result["composite_score"] == 100.0


def test_one_title_missing(scorer: Scorer, scoring_profile: dict) -> None:
    """One gold title missing → 0."""
    case = _make_case(["Alpha", "Beta", "Delta"])
    output = (
        '[1] «Alpha | text»\n'
        '[2] «Beta | text»\n'
        '[3] «Gamma | text»'
    )
    result = scorer.score_case(case, output, scoring_profile)
    assert result["composite_score"] == 0.0
    assert "delta" in [normalize_title(t) for t in result["score_breakdown"]["missing_titles"]]


def test_empty_output(scorer: Scorer, scoring_profile: dict) -> None:
    """Empty output → 0."""
    case = _make_case(["Alpha"])
    result = scorer.score_case(case, "", scoring_profile)
    assert result["composite_score"] == 0.0


def test_title_normalization_match(scorer: Scorer, scoring_profile: dict) -> None:
    """Title matching should be case-insensitive and strip articles."""
    case = _make_case(["The Quick Fox"])
    output = '[1] «the quick fox | passage»'
    result = scorer.score_case(case, output, scoring_profile)
    assert result["composite_score"] == 100.0


def test_validate_case_missing_titles(scorer: Scorer, scoring_profile: dict) -> None:
    case = EvalCase(
        case_id="bad-001",
        task_type="claim_verification",
        context={"claim": "test"},
        expected={},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.supporting_titles"):
        scorer.validate_case(case, scoring_profile)
