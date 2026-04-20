# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Shared test helpers for Hephaestus evaluation tests.

Provides reusable helpers that were previously duplicated across multiple
test files: TrackingProvider, write_dataset, and write_scorer.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List


class TrackingProvider:
    """Mock provider that tracks generate() calls and returns canned responses.

    Thread-safe: ``generate()`` can be called from multiple threads concurrently.
    """

    def __init__(self, responses: List[str] | None = None) -> None:
        self.calls: List[List[Dict[str, str]]] = []
        self._responses = responses or ["mock response"]
        self._call_index = 0
        self._lock = threading.Lock()

    def generate(self, messages: List[Dict[str, str]]) -> str:
        with self._lock:
            self.calls.append(messages)
            idx = min(self._call_index, len(self._responses) - 1)
            self._call_index += 1
        return self._responses[idx]


class DummyCompletions:
    """Mock completions endpoint for OpenAI-SDK-based provider tests."""

    def __init__(self) -> None:
        self.called_with: dict | None = None

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self.called_with = kwargs
        message = SimpleNamespace(content="ok")
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class DummyChat:
    def __init__(self, completions: DummyCompletions) -> None:
        self.completions = completions


class DummyClient:
    def __init__(self, completions: DummyCompletions) -> None:
        self.chat = DummyChat(completions)


def write_dataset(
    tmp_path: Path,
    cases: int = 1,
    expected: Dict[str, Any] | None = None,
) -> Path:
    """Write a JSONL dataset file with the given number of cases.

    Args:
        tmp_path: Pytest tmp_path directory.
        cases: Number of cases to generate.
        expected: Expected dict per case. Defaults to ``{}``.
    """
    if expected is None:
        expected = {}

    dataset = tmp_path / "cases.jsonl"
    lines = []
    for i in range(cases):
        case = {
            "case_id": f"c{i + 1}",
            "task_type": "security",
            "context": {"inputs.Name": f"user{i + 1}"},
            "expected": expected,
            "metadata": {},
        }
        lines.append(json.dumps(case))
    dataset.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dataset


def write_scorer(
    tmp_path: Path,
    composite_score: float = 100.0,
    breakdown_key: str = "quality",
) -> Path:
    """Write a minimal scorer module that returns a fixed composite score.

    Args:
        tmp_path: Pytest tmp_path directory.
        composite_score: The composite_score value the scorer returns.
        breakdown_key: The key used in score_breakdown.
    """
    scorer = tmp_path / "scorer.py"
    scorer.write_text(
        f"""\
from src.hephaestus.scoring.scorer import Scorer as BaseScorer

class Scorer(BaseScorer):
    def validate_case(self, case, scoring_profile):
        return None

    def score_case(self, case, output_text, scoring_profile):
        return {{
            'composite_score': {composite_score},
            'score_breakdown': {{'{breakdown_key}': {composite_score}}},
        }}
""",
        encoding="utf-8",
    )
    return scorer
