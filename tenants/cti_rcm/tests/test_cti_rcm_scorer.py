# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

faith = pytest.importorskip("faith", reason="faith package required for cti_rcm scorer tests")

from src.hephaestus.types import EvalCase  # noqa: E402
from tenants.cti_rcm.code.scorers.cti_rcm_scorer import Scorer  # noqa: E402


def _make_case(cwe_id: str, case_id: str = "test-001") -> EvalCase:
    return EvalCase(
        case_id=case_id,
        task_type="root_cause_mapping",
        context={"description": "CVE Description: some vulnerability"},
        expected={"cwe_id": cwe_id},
        metadata={"source": "AI4Sec/cti-bench", "subset": "cti-rcm"},
    )


@pytest.fixture()
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture()
def scoring_profile() -> dict[str, object]:
    return {}


# --- validate_case ---


def test_validate_case_valid(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("CWE-79")
    scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_cwe_id(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = EvalCase(
        case_id="bad-001",
        task_type="root_cause_mapping",
        context={"description": "some text"},
        expected={},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.cwe_id"):
        scorer.validate_case(case, scoring_profile)


# --- score_case: exact match ---


def test_exact_match_correct(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("CWE-79")
    result = scorer.score_case(case, "The answer is CWE-79", scoring_profile)
    assert result["composite_score"] == 100.0
    assert result["score_breakdown"]["exact_match"] == 100.0
    assert result["score_breakdown"]["answer_format"] == 100.0


def test_exact_match_wrong(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case("CWE-79")
    result = scorer.score_case(case, "The answer is CWE-89", scoring_profile)
    assert result["composite_score"] == 0.0
    assert result["score_breakdown"]["exact_match"] == 0.0


# --- answer format extraction ---


def test_proper_format_extraction(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """Standard CWE-NNN format is 'proper'."""
    case = _make_case("CWE-79")
    result = scorer.score_case(case, "The answer is CWE-79", scoring_profile)
    assert result["score_breakdown"]["answer_format"] == 100.0
    assert result["answer_format_label"] == "proper"


def test_improper_format_extraction(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """'CWE: 79' format is 'improper' but still extracts correctly."""
    case = _make_case("CWE-79")
    result = scorer.score_case(case, "CWE: 79", scoring_profile)
    assert result["composite_score"] == 100.0
    assert result["score_breakdown"]["answer_format"] == 50.0
    assert result["answer_format_label"] == "improper"


def test_no_match_invalid(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """Gibberish input yields no extraction and 'invalid' format."""
    case = _make_case("CWE-79")
    result = scorer.score_case(case, "I have no idea what the weakness is", scoring_profile)
    assert result["composite_score"] == 0.0
    assert result["score_breakdown"]["answer_format"] == 0.0


def test_multiple_cwe_ids_invalid(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """Multiple distinct CWE IDs → match_if_unique returns None → 'invalid'."""
    case = _make_case("CWE-79")
    result = scorer.score_case(case, "Could be CWE-79 or CWE-89", scoring_profile)
    assert result["composite_score"] == 0.0
    assert result["score_breakdown"]["answer_format"] == 0.0


def test_repeated_unique_cwe_proper(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """Same CWE repeated multiple times → unique → 'proper' match."""
    case = _make_case("CWE-79")
    result = scorer.score_case(case, "I think CWE-79 is correct. Yes, CWE-79.", scoring_profile)
    assert result["composite_score"] == 100.0
    assert result["score_breakdown"]["answer_format"] == 100.0


# --- case sensitivity ---


def test_case_insensitive_extraction(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    """Lowercase 'cwe-79' should be normalized to 'CWE-79'."""
    case = _make_case("CWE-79")
    result = scorer.score_case(case, "the answer is cwe-79", scoring_profile)
    assert result["composite_score"] == 100.0
