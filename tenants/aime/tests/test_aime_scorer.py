# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the aime tenant scorer."""

from __future__ import annotations

import pytest

from src.hephaestus.types import EvalCase
from tenants.aime.code.scorers.aime_scorer import Scorer, extract_integer_answer


def _make_case(answer: str, case_id: str = "test-001") -> EvalCase:
    return EvalCase(
        case_id=case_id,
        task_type="math_cot",
        context={"problem": "What is 2 + 2?"},
        expected={"answer": answer, "solution": ""},
        metadata={"source": "AI-MO/aimo-validation-aime", "split": "train"},
    )


@pytest.fixture()
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture()
def scoring_profile() -> dict[str, object]:
    return {}


# --- validate_case ---


def test_validate_case_valid(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("42")
    scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_answer(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = EvalCase(
        case_id="bad-001",
        task_type="math_cot",
        context={"problem": "What?"},
        expected={},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.answer"):
        scorer.validate_case(case, scoring_profile)


# --- extract_integer_answer ---


def test_extract_boxed_answer() -> None:
    assert extract_integer_answer(r"The answer is \boxed{42}.") == 42


def test_extract_boxed_takes_last() -> None:
    assert extract_integer_answer(r"First \boxed{1}, then \boxed{99}.") == 99


def test_extract_dspy_answer_field() -> None:
    text = "[[ ## reasoning ## ]]\nsome steps\n[[ ## answer ## ]]\n42\n"
    assert extract_integer_answer(text) == 42


def test_extract_bare_integer_fallback() -> None:
    assert extract_integer_answer("The answer is 42.") == 42


def test_extract_none_on_no_integer() -> None:
    assert extract_integer_answer("I don't know.") is None


def test_extract_prefers_boxed_over_bare() -> None:
    # Bare 99 appears after the boxed 42; boxed wins because it's the highest-priority match.
    assert extract_integer_answer(r"Reasoning leads to \boxed{42}. Distractor: 99") == 42


# --- score_case ---


def test_score_exact_match(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("42")
    result = scorer.score_case(case, r"The answer is \boxed{42}.", scoring_profile)
    assert result["composite_score"] == 100.0
    assert result["score_breakdown"]["exact_match"] == 100.0
    assert result["score_breakdown"]["parse_ok"] == 100.0


def test_score_wrong_answer(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("42")
    result = scorer.score_case(case, r"The answer is \boxed{99}.", scoring_profile)
    assert result["composite_score"] == 0.0
    assert result["score_breakdown"]["exact_match"] == 0.0
    assert result["score_breakdown"]["parse_ok"] == 100.0


def test_score_parse_failure(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("42")
    result = scorer.score_case(case, "I cannot solve this problem.", scoring_profile)
    assert result["composite_score"] == 0.0
    assert result["score_breakdown"]["exact_match"] == 0.0
    assert result["score_breakdown"]["parse_ok"] == 0.0


def test_non_integer_expected_raises(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("not-an-integer")
    with pytest.raises(ValueError, match="non-integer expected answer"):
        scorer.score_case(case, "42", scoring_profile)


# --- score_pipeline_case ---


def test_pipeline_scoring_uses_solve_step(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("42")
    step_outputs = {"solve": r"\boxed{42}"}
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 100.0


def test_pipeline_scoring_fallback_output_text(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("42")
    step_outputs = {"intermediate": "ignored"}
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile, output_text=r"\boxed{42}")
    assert result["composite_score"] == 100.0
