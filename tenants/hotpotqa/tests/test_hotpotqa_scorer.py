# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from src.hephaestus.types import EvalCase
from tenants.hotpotqa.code.scorers.hotpotqa_scorer import Scorer


def _make_case(answer: str, case_id: str = "test-001") -> EvalCase:
    return EvalCase(
        case_id=case_id,
        task_type="multihop_qa",
        context={"question": "What is the capital of France?"},
        expected={"answer": answer},
        metadata={"level": "hard", "source": "hotpotqa-fullwiki"},
    )


@pytest.fixture()
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture()
def scoring_profile() -> dict[str, object]:
    return {}


# --- validate_case ---


def test_validate_case_valid(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("Paris")
    scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_answer(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = EvalCase(
        case_id="bad-001",
        task_type="multihop_qa",
        context={"question": "What?"},
        expected={},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.answer"):
        scorer.validate_case(case, scoring_profile)


# --- score_case: exact match ---


def test_exact_match_correct(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("yes")
    result = scorer.score_case(case, "yes", scoring_profile)
    assert result["score_breakdown"]["exact_match"] == 100.0
    assert result["score_breakdown"]["f1"] == 100.0
    assert result["composite_score"] == 100.0


def test_exact_match_wrong(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("yes")
    result = scorer.score_case(case, "no", scoring_profile)
    assert result["score_breakdown"]["exact_match"] == 0.0


def test_normalization_articles(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """'the Dog' should match 'dog' after normalization."""
    case = _make_case("dog")
    result = scorer.score_case(case, "the Dog", scoring_profile)
    assert result["score_breakdown"]["exact_match"] == 100.0


def test_normalization_punctuation(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """'hello!' should match 'hello' after normalization."""
    case = _make_case("hello")
    result = scorer.score_case(case, "hello!", scoring_profile)
    assert result["score_breakdown"]["exact_match"] == 100.0


# --- score_case: F1 ---


def test_f1_exact(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("big brown dog")
    result = scorer.score_case(case, "big brown dog", scoring_profile)
    assert result["score_breakdown"]["f1"] == 100.0


def test_f1_partial_overlap(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """'big brown dog' vs 'big brown cat': 2 common tokens out of 3 each."""
    case = _make_case("big brown dog")
    result = scorer.score_case(case, "big brown cat", scoring_profile)
    # precision = 2/3, recall = 2/3, f1 = 2/3 → 66.67
    f1 = result["score_breakdown"]["f1"]
    assert abs(f1 - 66.67) < 0.1


def test_f1_no_overlap(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("cat")
    result = scorer.score_case(case, "dog", scoring_profile)
    assert result["score_breakdown"]["f1"] == 0.0


def test_f1_empty_prediction(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("Paris")
    result = scorer.score_case(case, "", scoring_profile)
    assert result["score_breakdown"]["f1"] == 0.0
    assert result["score_breakdown"]["exact_match"] == 0.0


def test_f1_empty_expected(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """Both empty → exact match is 100 but f1 is 0 (matches DSPy behavior)."""
    case = _make_case("")
    result = scorer.score_case(case, "", scoring_profile)
    assert result["score_breakdown"]["exact_match"] == 100.0
    assert result["score_breakdown"]["f1"] == 0.0


# --- composite score ---


def test_composite_score_formula(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """Composite = pure EM (matching GEPA paper's answer_exact_match metric)."""
    case = _make_case("big brown dog")
    result = scorer.score_case(case, "big brown cat", scoring_profile)
    em = result["score_breakdown"]["exact_match"]
    assert result["composite_score"] == em


# --- score_pipeline_case ---


def test_pipeline_scoring_uses_answer_step(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """score_pipeline_case should use step_outputs['answer'] as the output text."""
    case = _make_case("Paris")
    step_outputs = {
        "query_hop1": "some query",
        "summarize_hop1": "some summary",
        "answer": "Paris",
    }
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["score_breakdown"]["exact_match"] == 100.0


def test_pipeline_scoring_fallback_to_output_text(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """When 'answer' key is missing, prefer output_text over last step output."""
    case = _make_case("Paris")
    step_outputs = {"query_hop1": "some query"}
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile, output_text="Paris")
    assert result["score_breakdown"]["exact_match"] == 100.0


def test_pipeline_scoring_fallback_to_last_step(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """When 'answer' key and output_text are missing, fall back to last step output."""
    case = _make_case("Paris")
    step_outputs = {
        "query_hop1": "some query",
        "final_output": "Paris",
    }
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["score_breakdown"]["exact_match"] == 100.0


def test_pipeline_scoring_empty_raises(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """When step_outputs is empty and no output_text, raise ValueError."""
    case = _make_case("Paris")
    with pytest.raises(ValueError, match="empty step_outputs"):
        scorer.score_pipeline_case(case, {}, scoring_profile)
