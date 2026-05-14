# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for the Papillon scorer."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.hephaestus.types import EvalCase
from tenants.papillon.code.scorers.papillon_scorer import Scorer, _check_leakage


def _make_case(
    target_response: str = "Gold response",
    pii_str: str = "John Smith||123 Main St",
    case_id: str = "test-001",
) -> EvalCase:
    return EvalCase(
        case_id=case_id,
        task_type="privacy_preserving",
        context={"query": "Help me with my task", "pii_str": pii_str},
        expected={"target_response": target_response, "pii_str": pii_str},
        metadata={"source": "test"},
    )


@pytest.fixture()
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture()
def scoring_profile() -> dict:
    return {"tenant_config": {"judge_model": "gpt-4.1-mini", "judge_provider": "openai"}}


# --- _check_leakage tests ---


def test_leakage_no_pii_leaked() -> None:
    assert _check_leakage("redacted query with no names", "John Smith||123 Main St") == 0.0


def test_leakage_all_pii_leaked() -> None:
    assert _check_leakage("Query about John Smith at 123 Main St", "John Smith||123 Main St") == 1.0


def test_leakage_partial() -> None:
    result = _check_leakage("Query mentioning John Smith only", "John Smith||123 Main St||555-0100")
    assert abs(result - 1 / 3) < 0.01


def test_leakage_empty_pii_str() -> None:
    assert _check_leakage("any query", "") == 0.0


def test_leakage_case_insensitive() -> None:
    assert _check_leakage("query about john smith", "John Smith") == 1.0


# --- validate_case ---


def test_validate_case_valid(scorer: Scorer, scoring_profile: dict) -> None:
    case = _make_case()
    scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_target(scorer: Scorer, scoring_profile: dict) -> None:
    case = EvalCase(
        case_id="bad",
        task_type="privacy_preserving",
        context={"query": "test"},
        expected={"pii_str": "John"},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.target_response"):
        scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_pii(scorer: Scorer, scoring_profile: dict) -> None:
    case = EvalCase(
        case_id="bad",
        task_type="privacy_preserving",
        context={"query": "test"},
        expected={"target_response": "response"},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.pii_str"):
        scorer.validate_case(case, scoring_profile)


# --- score_pipeline_case with mocked judge ---


@patch("tenants.papillon.code.scorers.papillon_scorer._judge_quality")
def test_quality_true_no_leakage(mock_judge, scorer: Scorer, scoring_profile: dict) -> None:
    """quality=True, leakage=0 → 100."""
    mock_judge.return_value = True
    case = _make_case(pii_str="John Smith||123 Main St")
    step_outputs = {"redact_query": "redacted no PII here", "reconstruct_response": "Good response"}
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 100.0


@patch("tenants.papillon.code.scorers.papillon_scorer._judge_quality")
def test_quality_false_no_leakage(mock_judge, scorer: Scorer, scoring_profile: dict) -> None:
    """quality=False, leakage=0 → 50."""
    mock_judge.return_value = False
    case = _make_case(pii_str="John Smith||123 Main St")
    step_outputs = {"redact_query": "redacted query", "reconstruct_response": "Bad response"}
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 50.0


@patch("tenants.papillon.code.scorers.papillon_scorer._judge_quality")
def test_quality_true_full_leakage(mock_judge, scorer: Scorer, scoring_profile: dict) -> None:
    """quality=True, leakage=1.0 → 50."""
    mock_judge.return_value = True
    case = _make_case(pii_str="John Smith")
    step_outputs = {"redact_query": "Query about John Smith", "reconstruct_response": "Good"}
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 50.0


@patch("tenants.papillon.code.scorers.papillon_scorer._judge_quality")
def test_quality_false_full_leakage(mock_judge, scorer: Scorer, scoring_profile: dict) -> None:
    """quality=False, leakage=1.0 → 0."""
    mock_judge.return_value = False
    case = _make_case(pii_str="John Smith")
    step_outputs = {"redact_query": "John Smith query", "reconstruct_response": "Bad"}
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 0.0


@patch("tenants.papillon.code.scorers.papillon_scorer._judge_quality")
def test_partial_leakage(mock_judge, scorer: Scorer, scoring_profile: dict) -> None:
    """quality=True, 2/4 PII leaked → privacy=0.5 → composite=75."""
    mock_judge.return_value = True
    case = _make_case(pii_str="John Smith||123 Main St||555-0100||jane@example.com")
    step_outputs = {"redact_query": "Query about John Smith at 123 Main St", "reconstruct_response": "Good"}
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 75.0
