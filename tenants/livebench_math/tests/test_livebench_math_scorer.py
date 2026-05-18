# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the LiveBench Math scorer."""

from __future__ import annotations

import pytest

pytest.importorskip("sympy", reason="livebench_math tests require sympy")

from src.hephaestus.types import EvalCase  # noqa: E402
from tenants.livebench_math.code.scorers.livebench_math_scorer import Scorer  # noqa: E402


def _make_case(
    question_d: dict,
    case_id: str = "test-001",
) -> EvalCase:
    return EvalCase(
        case_id=case_id,
        task_type="math",
        context={"question": question_d["turns"][0]},
        expected={"question_d": question_d},
        metadata={"source": "livebench/math", "task": question_d.get("task", "")},
    )


def _amc_question_d(ground_truth: str = "C") -> dict:
    return {
        "question_id": "amc_test_001",
        "task": "math_competitions",
        "subtask": "amc_2024",
        "category": "math",
        "turns": [
            "What is 2+2? \\textbf{(A)}~3\\qquad\\textbf{(B)}~5"
            "\\qquad\\textbf{(C)}~4\\qquad\\textbf{(D)}~6\\qquad\\textbf{(E)}~7"
        ],
        "ground_truth": ground_truth,
    }


def _aime_question_d(ground_truth: str = "42") -> dict:
    return {
        "question_id": "aime_test_001",
        "task": "math_competitions",
        "subtask": "aime_2024",
        "category": "math",
        "turns": ["Find the integer value of the expression..."],
        "ground_truth": ground_truth,
    }


def _olympiad_question_d(ground_truth: str = "0,1,2,3,4,5") -> dict:
    return {
        "question_id": "imo_test_001",
        "task": "math_competitions",
        "subtask": "imo_2024",
        "category": "math",
        "turns": ["Arrange the following proof steps..."],
        "ground_truth": ground_truth,
    }


@pytest.fixture()
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture()
def scoring_profile() -> dict:
    return {}


# --- validate_case ---


def test_validate_case_valid(scorer: Scorer, scoring_profile: dict) -> None:
    case = _make_case(_amc_question_d())
    scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_question_d(scorer: Scorer, scoring_profile: dict) -> None:
    case = EvalCase(
        case_id="bad-001",
        task_type="math",
        context={"question": "What?"},
        expected={},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.question_d"):
        scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_ground_truth(scorer: Scorer, scoring_profile: dict) -> None:
    qd = _amc_question_d()
    del qd["ground_truth"]
    case = _make_case(qd)
    with pytest.raises(ValueError, match="missing expected.question_d.ground_truth"):
        scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_task(scorer: Scorer, scoring_profile: dict) -> None:
    qd = _amc_question_d()
    del qd["task"]
    case = _make_case(qd)
    with pytest.raises(ValueError, match="missing expected.question_d.task"):
        scorer.validate_case(case, scoring_profile)


# --- AMC scoring ---


def test_amc_correct_boxed(scorer: Scorer, scoring_profile: dict) -> None:
    """AMC answer with \\boxed{C} should score 100."""
    case = _make_case(_amc_question_d("C"))
    result = scorer.score_case(case, "The answer is \\boxed{C}", scoring_profile)
    assert result["composite_score"] == 100.0


def test_amc_correct_repeated_letter(scorer: Scorer, scoring_profile: dict) -> None:
    """AMC answer with repeated letter pattern should score 100."""
    case = _make_case(_amc_question_d("B"))
    result = scorer.score_case(case, "I think the answer is BBBBB", scoring_profile)
    assert result["composite_score"] == 100.0


def test_amc_wrong_answer(scorer: Scorer, scoring_profile: dict) -> None:
    """Wrong AMC answer should score 0."""
    case = _make_case(_amc_question_d("C"))
    result = scorer.score_case(case, "The answer is \\boxed{A}", scoring_profile)
    assert result["composite_score"] == 0.0


def test_amc_correct_last_line(scorer: Scorer, scoring_profile: dict) -> None:
    """AMC answer where last line is just the letter should score 100."""
    case = _make_case(_amc_question_d("D"))
    result = scorer.score_case(case, "After calculation...\nD", scoring_profile)
    assert result["composite_score"] == 100.0


# --- AIME scoring ---


def test_aime_correct_in_last_50(scorer: Scorer, scoring_profile: dict) -> None:
    """AIME answer present in last 50 chars should score 100."""
    case = _make_case(_aime_question_d("42"))
    result = scorer.score_case(case, "The final answer is 42.", scoring_profile)
    assert result["composite_score"] == 100.0


def test_aime_correct_boxed(scorer: Scorer, scoring_profile: dict) -> None:
    """AIME answer in \\boxed{} in last 50 chars should score 100."""
    case = _make_case(_aime_question_d("157"))
    result = scorer.score_case(case, "Therefore \\boxed{157}", scoring_profile)
    assert result["composite_score"] == 100.0


def test_aime_wrong_answer(scorer: Scorer, scoring_profile: dict) -> None:
    """Wrong AIME answer should score 0."""
    case = _make_case(_aime_question_d("42"))
    result = scorer.score_case(case, "The final answer is 99.", scoring_profile)
    assert result["composite_score"] == 0.0


def test_aime_answer_too_early(scorer: Scorer, scoring_profile: dict) -> None:
    """AIME answer present but not in last 50 chars should score 0."""
    case = _make_case(_aime_question_d("42"))
    output = "The answer is 42." + " " * 100 + "done"
    result = scorer.score_case(case, output, scoring_profile)
    assert result["composite_score"] == 0.0


# --- Olympiad scoring ---


def test_olympiad_exact_match(scorer: Scorer, scoring_profile: dict) -> None:
    """Exact olympiad sequence match should score 100."""
    case = _make_case(_olympiad_question_d("0,1,2,3,4,5"))
    result = scorer.score_case(case, "answer: 0, 1, 2, 3, 4, 5", scoring_profile)
    assert result["composite_score"] == 100.0


def test_olympiad_partial_match(scorer: Scorer, scoring_profile: dict) -> None:
    """Partial olympiad match should give fractional score."""
    case = _make_case(_olympiad_question_d("0,1,2,3,4,5"))
    result = scorer.score_case(case, "answer: 0, 1, 2, 3, 5, 4", scoring_profile)
    assert 0 < result["composite_score"] < 100.0


# --- Think tag stripping ---


def test_think_tags_stripped(scorer: Scorer, scoring_profile: dict) -> None:
    """<think> tags should be stripped before scoring."""
    case = _make_case(_aime_question_d("42"))
    output = "<think>Let me think about this...</think>The answer is 42."
    result = scorer.score_case(case, output, scoring_profile)
    assert result["composite_score"] == 100.0


# --- Error handling ---


def test_unimplemented_task_returns_zero(scorer: Scorer, scoring_profile: dict) -> None:
    """Unknown task type should score 0 without crashing."""
    qd = {
        "question_id": "unknown_001",
        "task": "unknown_task",
        "subtask": "unknown_subtask",
        "category": "math",
        "turns": ["What is this?"],
        "ground_truth": "42",
    }
    case = _make_case(qd)
    result = scorer.score_case(case, "42", scoring_profile)
    assert result["composite_score"] == 0.0
    assert "error" in result["score_breakdown"]
