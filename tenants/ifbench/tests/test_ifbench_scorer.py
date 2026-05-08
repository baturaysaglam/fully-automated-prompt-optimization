# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the ifbench scorer.

The scorer depends on ``gepa_artifact...instructions_registry`` plus nltk,
spacy, syllapy, emoji, and immutabledict. We stub ``INSTRUCTION_DICT`` in-
process to exercise the scorer logic without needing those deps.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from src.hephaestus.types import EvalCase
from tenants.ifbench.code.scorers import ifbench_scorer


class _FakeInstruction:
    """Stub instruction class that returns a fixed follow/no-follow based on *name*.

    Constructed via ``_FakeInstruction(name)``; matches the API the scorer
    expects: ``build_description(**kwargs)``, ``get_instruction_args()`` (returns
    an empty list so the prompt-injection branch is skipped), and
    ``check_following(response)``.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def build_description(self, **_: Any) -> str:
        return f"desc:{self.name}"

    def get_instruction_args(self) -> Optional[List[str]]:
        return None

    def check_following(self, response: str) -> bool:
        # Our test instruction ids encode the expected substring.
        # ``pass_if_contains:foo`` returns True iff "foo" in response.
        if self.name.startswith("pass_if_contains:"):
            token = self.name.split(":", 1)[1]
            return token in response
        if self.name == "always_pass":
            return True
        return False


def _make_case(instruction_ids: List[str], kwargs: List[Dict[str, Any]] | None = None) -> EvalCase:
    return EvalCase(
        case_id="ifbench-test-0",
        task_type="instruction_following",
        context={"prompt": "Write a response following the rules."},
        expected={
            "instruction_id_list": instruction_ids,
            "kwargs": kwargs if kwargs is not None else [{} for _ in instruction_ids],
            "key": 0,
        },
        metadata={"source": "IFBench"},
    )


@pytest.fixture(autouse=True)
def _inject_fake_registry() -> None:
    fake_dict = {
        name: _FakeInstruction
        for name in (
            "pass_if_contains:apple",
            "pass_if_contains:banana",
            "always_pass",
            "always_fail",
        )
    }
    # We need the scorer's runtime class lookup to return _FakeInstruction when
    # called with (instruction_id). The scorer does `cls = INSTRUCTION_DICT[id]; cls(id)`.
    # Our fake class is constructed with the id, so a single-class dict works.
    ifbench_scorer._set_instruction_dict_for_testing(fake_dict)
    yield
    ifbench_scorer._set_instruction_dict_for_testing(None)


@pytest.fixture()
def scorer() -> ifbench_scorer.Scorer:
    return ifbench_scorer.Scorer()


@pytest.fixture()
def scoring_profile() -> Dict[str, Any]:
    return {}


# --- validate_case ---


def test_validate_case_valid(scorer: ifbench_scorer.Scorer, scoring_profile: Dict[str, Any]) -> None:
    scorer.validate_case(_make_case(["always_pass"]), scoring_profile)


def test_validate_case_missing_id_list(
    scorer: ifbench_scorer.Scorer, scoring_profile: Dict[str, Any]
) -> None:
    case = EvalCase(
        case_id="bad",
        task_type="instruction_following",
        context={"prompt": "x"},
        expected={"kwargs": []},
        metadata={},
    )
    with pytest.raises(ValueError, match="missing expected.instruction_id_list"):
        scorer.validate_case(case, scoring_profile)


# --- score_case ---


def test_all_instructions_pass(scorer: ifbench_scorer.Scorer, scoring_profile: Dict[str, Any]) -> None:
    case = _make_case(["always_pass", "pass_if_contains:apple"])
    result = scorer.score_case(case, "I ate an apple today.", scoring_profile)
    assert result["composite_score"] == 100.0
    assert result["score_breakdown"]["instruction_pass_rate"] == 100.0
    assert result["score_breakdown"]["instructions_evaluated"] == 2.0
    assert result["score_breakdown"]["scorer_ok"] == 100.0


def test_partial_pass(scorer: ifbench_scorer.Scorer, scoring_profile: Dict[str, Any]) -> None:
    case = _make_case(["always_pass", "pass_if_contains:banana"])
    result = scorer.score_case(case, "Only apples here.", scoring_profile)
    # 1 of 2 satisfied → 50.0
    assert result["composite_score"] == 50.0


def test_all_fail(scorer: ifbench_scorer.Scorer, scoring_profile: Dict[str, Any]) -> None:
    case = _make_case(["always_fail", "pass_if_contains:banana"])
    result = scorer.score_case(case, "apple pie", scoring_profile)
    assert result["composite_score"] == 0.0


def test_asterisk_stripping_helps(
    scorer: ifbench_scorer.Scorer, scoring_profile: Dict[str, Any]
) -> None:
    """The scorer tries an asterisk-stripped variant; 'appl*e' with asterisks
    stripped becomes 'apple', which satisfies pass_if_contains:apple."""
    case = _make_case(["pass_if_contains:apple"])
    result = scorer.score_case(case, "I ate an a*pple today.", scoring_profile)
    # With '*' stripped the response contains 'apple' → pass.
    assert result["composite_score"] == 100.0


def test_empty_instruction_list_returns_zero(
    scorer: ifbench_scorer.Scorer, scoring_profile: Dict[str, Any]
) -> None:
    case = _make_case([])
    result = scorer.score_case(case, "anything", scoring_profile)
    assert result["composite_score"] == 0.0
    assert result["score_breakdown"]["instructions_evaluated"] == 0.0


# --- score_pipeline_case ---


def test_pipeline_uses_ensure_correct_response(
    scorer: ifbench_scorer.Scorer, scoring_profile: Dict[str, Any]
) -> None:
    case = _make_case(["pass_if_contains:banana"])
    # Draft says apple, revised says banana. Scorer should read the revised step.
    step_outputs = {
        "generate_response": "My draft mentions apple.",
        "ensure_correct_response": "My final mentions banana.",
    }
    result = scorer.score_pipeline_case(case, step_outputs, scoring_profile)
    assert result["composite_score"] == 100.0


# --- import-error surface ---


def test_score_case_import_error_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """With GEPA_ARTIFACT_PATH unset and cached dict cleared, score_case raises ImportError."""
    ifbench_scorer._set_instruction_dict_for_testing(None)
    monkeypatch.delenv("GEPA_ARTIFACT_PATH", raising=False)
    scorer_instance = ifbench_scorer.Scorer()
    case = _make_case(["always_pass"])
    with pytest.raises(ImportError, match="GEPA_ARTIFACT_PATH is unset"):
        scorer_instance.score_case(case, "anything", {})
