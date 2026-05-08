# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the livebench_math tenant scorer.

The scorer wraps ``calculate_livebench_score`` from the GEPA artifact. Unit
tests mock that function to exercise scorer routing and error handling without
requiring ``GEPA_ARTIFACT_PATH`` or heavy deps. An integration test that runs
the real function is added under the ``requires_gepa_artifact`` marker.
"""

from __future__ import annotations

from typing import Any, Callable

import pytest

from src.hephaestus.types import EvalCase
from tenants.livebench_math.code.scorers import livebench_math_scorer as scorer_module


def _make_case(ground_truth: str, task: str = "aime_2023", subtask: str | None = None) -> EvalCase:
    question_d: dict[str, Any] = {
        "question_id": "test-001",
        "turns": ["What is 2+2?"],
        "ground_truth": ground_truth,
        "task": task,
    }
    if subtask:
        question_d["subtask"] = subtask
    return EvalCase(
        case_id="livebench-math-train-0",
        task_type="livebench_math_cot",
        context={"question": "What is 2+2?"},
        expected={"answer": ground_truth},
        metadata={
            "source": "livebench/math",
            "split": "train",
            "task": task,
            "question_d": question_d,
        },
    )


@pytest.fixture(autouse=True)
def _reset_cached_score_fn() -> None:
    """Reset the module-level cached score fn so each test can inject its own."""
    scorer_module._livebench_score_fn = None
    yield
    scorer_module._livebench_score_fn = None


@pytest.fixture()
def scoring_profile() -> dict[str, Any]:
    return {}


def _patch_score_fn(fn: Callable) -> Any:
    scorer_module._livebench_score_fn = fn
    return fn


# --- validate_case ---


def test_validate_case_valid(scoring_profile: dict[str, Any]) -> None:
    s = scorer_module.Scorer()
    s.validate_case(_make_case("4"), scoring_profile)


def test_validate_case_missing_answer() -> None:
    s = scorer_module.Scorer()
    case = EvalCase(
        case_id="bad",
        task_type="livebench_math_cot",
        context={"question": "x"},
        expected={},
        metadata={"question_d": {"task": "aime"}},
    )
    with pytest.raises(ValueError, match="missing expected.answer"):
        s.validate_case(case, {})


def test_validate_case_missing_question_d() -> None:
    s = scorer_module.Scorer()
    case = EvalCase(
        case_id="bad",
        task_type="livebench_math_cot",
        context={"question": "x"},
        expected={"answer": "4"},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing metadata.question_d"):
        s.validate_case(case, {})


# --- score_case: routing + normalization ---


def test_score_binary_1_becomes_100(scoring_profile: dict[str, Any]) -> None:
    _patch_score_fn(lambda q, a, debug=False: (1, ""))
    s = scorer_module.Scorer()
    result = s.score_case(_make_case("4"), "My answer is 4.", scoring_profile)
    assert result["composite_score"] == 100.0
    assert result["score_breakdown"]["livebench_score"] == 100.0
    assert result["score_breakdown"]["scorer_ok"] == 100.0


def test_score_binary_0_becomes_0(scoring_profile: dict[str, Any]) -> None:
    _patch_score_fn(lambda q, a, debug=False: (0, ""))
    s = scorer_module.Scorer()
    result = s.score_case(_make_case("4"), "My answer is 5.", scoring_profile)
    assert result["composite_score"] == 0.0
    assert result["score_breakdown"]["livebench_score"] == 0.0
    assert result["score_breakdown"]["scorer_ok"] == 100.0


def test_score_partial_credit_passthrough(scoring_profile: dict[str, Any]) -> None:
    # IMO/USAMO proof-rearrangement returns an already-percentage value (e.g. 42.5).
    _patch_score_fn(lambda q, a, debug=False: (42.5, ""))
    s = scorer_module.Scorer()
    result = s.score_case(_make_case("proof..."), "partial proof", scoring_profile)
    assert result["composite_score"] == 42.5


def test_score_scorer_exception_returns_zero(scoring_profile: dict[str, Any]) -> None:
    def raising(_q: Any, _a: Any, debug: bool = False) -> Any:
        raise RuntimeError("upstream failure")

    _patch_score_fn(raising)
    s = scorer_module.Scorer()
    result = s.score_case(_make_case("4"), "anything", scoring_profile)
    assert result["composite_score"] == 0.0
    assert result["score_breakdown"]["scorer_ok"] == 0.0


def test_score_clamps_above_100(scoring_profile: dict[str, Any]) -> None:
    _patch_score_fn(lambda q, a, debug=False: (150.0, ""))
    s = scorer_module.Scorer()
    result = s.score_case(_make_case("x"), "x", scoring_profile)
    assert result["composite_score"] == 100.0


# --- score_pipeline_case ---


def test_pipeline_uses_solve_step(scoring_profile: dict[str, Any]) -> None:
    _patch_score_fn(lambda q, a, debug=False: (1, ""))
    s = scorer_module.Scorer()
    step_outputs = {"solve": "answer 4"}
    result = s.score_pipeline_case(_make_case("4"), step_outputs, scoring_profile)
    assert result["composite_score"] == 100.0


# --- import-error surface ---


def test_import_error_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """If GEPA_ARTIFACT_PATH is unset and scorer is called, a clear ImportError is raised."""
    scorer_module._livebench_score_fn = None
    monkeypatch.delenv("GEPA_ARTIFACT_PATH", raising=False)
    s = scorer_module.Scorer()
    with pytest.raises(ImportError, match="GEPA_ARTIFACT_PATH is unset"):
        s.score_case(_make_case("4"), "anything", {})
