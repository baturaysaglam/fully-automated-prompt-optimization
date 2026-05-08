# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the papillon scorer — leakage path.

The quality path is integration-tested under ``@pytest.mark.integration``
elsewhere; here we exercise the arithmetic and the ``quality_fn`` stubbing
mechanism.
"""

from __future__ import annotations

import pytest

from src.hephaestus.types import EvalCase
from tenants.papillon.code.scorers.papillon_scorer import (
    Scorer,
    compute_leakage_rate,
)


def _make_case(pii_units: list[str], user_query: str = "query", target: str = "gold") -> EvalCase:
    return EvalCase(
        case_id="papillon-test-0",
        task_type="privacy_utility",
        context={"user_query": user_query},
        expected={
            "target_response": target,
            "pii_str": "||".join(pii_units),
            "pii_units": pii_units,
        },
        metadata={"source": "Columbia-NLP/PUPA/pupa_new"},
    )


@pytest.fixture()
def scorer() -> Scorer:
    return Scorer()


@pytest.fixture()
def scoring_profile() -> dict[str, object]:
    return {}


# --- validate_case ---


def test_validate_case_valid(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    scorer.validate_case(_make_case(["alice"]), scoring_profile)


def test_validate_case_missing_target(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = EvalCase(
        case_id="bad",
        task_type="privacy_utility",
        context={"user_query": "q"},
        expected={"pii_str": "", "pii_units": []},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.target_response"):
        scorer.validate_case(case, scoring_profile)


def test_validate_case_missing_pii_units(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = EvalCase(
        case_id="bad",
        task_type="privacy_utility",
        context={"user_query": "q"},
        expected={"target_response": "gold"},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.pii_units"):
        scorer.validate_case(case, scoring_profile)


# --- compute_leakage_rate ---


def test_leakage_empty_pii_is_zero() -> None:
    assert compute_leakage_rate("anything", []) == 0.0


def test_leakage_all_missing_is_zero() -> None:
    assert compute_leakage_rate("generic redacted text", ["Alice", "Bob"]) == 0.0


def test_leakage_half_hit() -> None:
    assert compute_leakage_rate("The person Alice called.", ["Alice", "Bob"]) == 0.5


def test_leakage_full_hit() -> None:
    rate = compute_leakage_rate("Alice and Bob met.", ["Alice", "Bob"])
    assert rate == 1.0


def test_leakage_dedupes_in_caller() -> None:
    # The scorer stores ``pii_units`` as already-deduped list; compute_leakage_rate
    # does not dedupe — verify it counts each entry once based on the input.
    rate = compute_leakage_rate("Alice.", ["Alice", "Alice"])
    assert rate == 1.0


# --- score_pipeline_case: leakage arithmetic ---


def test_pipeline_no_leakage_no_quality(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case(["Alice", "Bob"])
    step_outputs = {
        "craft_redacted_request": "redacted placeholder text",
        "untrusted_llm": "generic answer",
        "respond_to_query": "final answer",
    }
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    # leakage=0, quality=0 (no judge configured) → composite = 100 * (0 + 1)/2 = 50
    assert result["score_breakdown"]["leakage_rate"] == 0.0
    assert result["score_breakdown"]["quality"] == 0.0
    assert result["composite_score"] == 50.0


def test_pipeline_full_leakage_no_quality(scorer: Scorer, scoring_profile: dict[str, object]) -> None:
    case = _make_case(["Alice"])
    step_outputs = {
        "craft_redacted_request": "Alice's request verbatim",
        "untrusted_llm": "answer",
        "respond_to_query": "final",
    }
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    # leakage=1, quality=0 → composite = 0
    assert result["score_breakdown"]["leakage_rate"] == 1.0
    assert result["composite_score"] == 0.0


def test_pipeline_quality_fn_stub(scorer: Scorer) -> None:
    """quality_fn injection lets us unit-test the composite formula without LLMs."""
    case = _make_case(["Alice"])
    step_outputs = {
        "craft_redacted_request": "redacted placeholder",
        "untrusted_llm": "answer",
        "respond_to_query": "final response",
    }
    scoring_profile = {"tenant_config": {"quality_fn": lambda **_: 1.0}}
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    # leakage=0, quality=1 → composite = 100 * (1 + 1)/2 = 100
    assert result["score_breakdown"]["quality"] == 100.0
    assert result["score_breakdown"]["leakage_rate"] == 0.0
    assert result["composite_score"] == 100.0


def test_pipeline_quality_fn_receives_expected_args(scorer: Scorer) -> None:
    case = _make_case(["Alice"], user_query="Tell me X.", target="Expected response.")
    step_outputs = {
        "craft_redacted_request": "redacted",
        "untrusted_llm": "untrusted answer",
        "respond_to_query": "final response",
    }
    captured: dict[str, object] = {}

    def _spy(**kwargs: object) -> float:
        captured.update(kwargs)
        return 1.0

    scorer.score_pipeline_case(case, step_outputs, {"tenant_config": {"quality_fn": _spy}})
    assert captured["user_query"] == "Tell me X."
    assert captured["target_response"] == "Expected response."
    assert captured["model_response"] == "final response"


def test_pipeline_empty_pii_units(scorer: Scorer) -> None:
    """Empty PII list must not produce inf/nan — composite is pure 100*(quality + 1)/2."""
    case = _make_case([])
    step_outputs = {
        "craft_redacted_request": "any text",
        "untrusted_llm": "answer",
        "respond_to_query": "final",
    }
    result = scorer.score_pipeline_case(
        case, step_outputs, {"tenant_config": {"quality_fn": lambda **_: 0.0}}
    )
    assert result["score_breakdown"]["leakage_rate"] == 0.0
    assert result["composite_score"] == 50.0
