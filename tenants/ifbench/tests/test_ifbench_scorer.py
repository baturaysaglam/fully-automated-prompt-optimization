# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the IFBench scorer."""

from __future__ import annotations

import pytest

from src.hephaestus.types import EvalCase
from tenants.ifbench.code.scorers.ifbench_scorer import Scorer


def _make_case(
    instruction_id_list: list[str],
    kwargs: list[dict],
    prompt: str = "Write a response.",
    case_id: str = "test-001",
) -> EvalCase:
    return EvalCase(
        case_id=case_id,
        task_type="instruction_following",
        context={"prompt": prompt},
        expected={"instruction_id_list": instruction_id_list, "kwargs": kwargs},
        metadata={"source": "test"},
    )


@pytest.fixture()
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture()
def scoring_profile() -> dict:
    return {}


# --- validate_case ---


def test_validate_case_valid(scorer: Scorer, scoring_profile: dict) -> None:
    case = _make_case(["count:word_count_range"], [{"min_words": 10, "max_words": 50}])
    scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_instruction_id_list(scorer: Scorer, scoring_profile: dict) -> None:
    case = EvalCase(
        case_id="bad-001",
        task_type="instruction_following",
        context={"prompt": "test"},
        expected={"kwargs": [{}]},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.instruction_id_list"):
        scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_kwargs(scorer: Scorer, scoring_profile: dict) -> None:
    case = EvalCase(
        case_id="bad-002",
        task_type="instruction_following",
        context={"prompt": "test"},
        expected={"instruction_id_list": ["count:word_count_range"]},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.kwargs"):
        scorer.validate_case(case, scoring_profile)


# --- score_case with mocked instruction checks ---


def test_all_instructions_followed(scorer: Scorer, scoring_profile: dict) -> None:
    """All instructions met → 100."""
    case = _make_case(
        ["count:word_count_range"],
        [{"min_words": 1, "max_words": 1000}],
    )
    result = scorer.score_case(case, "Hello world this is a test response", scoring_profile)
    assert result["composite_score"] == 100.0


def test_no_instructions_returns_zero(scorer: Scorer, scoring_profile: dict) -> None:
    """Empty instruction list → 0 score."""
    case = _make_case([], [])
    result = scorer.score_case(case, "Some text", scoring_profile)
    assert result["composite_score"] == 0.0


# --- composite score structure ---


def test_score_breakdown_keys(scorer: Scorer, scoring_profile: dict) -> None:
    """Score breakdown should have expected keys."""
    case = _make_case(
        ["count:word_count_range"],
        [{"min_words": 1, "max_words": 1000}],
    )
    result = scorer.score_case(case, "Hello world", scoring_profile)
    breakdown = result["score_breakdown"]
    assert "instruction_adherence" in breakdown
    assert "instructions_total" in breakdown
    assert "instructions_followed" in breakdown
    assert "feedback" in breakdown


def test_partial_score(scorer: Scorer, scoring_profile: dict) -> None:
    """Word count within range should pass, but very restrictive range should fail."""
    case = _make_case(
        ["count:word_count_range", "count:word_count_range"],
        [{"min_words": 1, "max_words": 1000}, {"min_words": 999, "max_words": 1000}],
    )
    result = scorer.score_case(case, "Hello world", scoring_profile)
    assert result["composite_score"] == 50.0
