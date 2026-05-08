# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""LiveBench-Math scorer wrapping GEPA's ``calculate_livebench_score``.

GEPA's metric (``gepa_artifact/benchmarks/livebench_math/__init__.py:metric``) is:

    question_d = example['question_d']
    score, _ = calculate_livebench_score(question_d, prediction.answer)
    return score

We port that, with two wrinkles:

- ``calculate_livebench_score`` lives in ``livebenchmath_utils`` inside the
  gepa-artifact repo. We import it at call-time via ``GEPA_ARTIFACT_PATH``
  (env var). If the env var is unset or the module cannot be imported,
  raise a clear ``ImportError`` naming the required env var and missing deps.
- The raw score is already in ``[0, 1]`` for binary tasks and ``[0, 100]``
  for partial-credit proof-rearrangement tasks. We renormalize to ``[0, 100]``
  by treating any value ``> 1`` as a percentage and any value ``<= 1`` as a
  fraction (this matches how GEPA's upstream `metric()` sums these).
"""

from __future__ import annotations

import os
import sys
import threading
from typing import Any, Callable, Dict, Optional

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase

_livebench_score_fn: Optional[Callable] = None
_import_lock = threading.Lock()


def _load_calculate_livebench_score() -> Callable:
    """Lazy-load ``calculate_livebench_score`` from the GEPA artifact.

    Raises ``ImportError`` with a clear remediation message if the env var
    ``GEPA_ARTIFACT_PATH`` is unset or the module cannot be imported.
    """
    global _livebench_score_fn
    if _livebench_score_fn is not None:
        return _livebench_score_fn
    with _import_lock:
        if _livebench_score_fn is not None:
            return _livebench_score_fn

        gepa_path = os.environ.get("GEPA_ARTIFACT_PATH")
        if not gepa_path:
            raise ImportError(
                "GEPA_ARTIFACT_PATH is unset. The livebench_math scorer wraps "
                "gepa_artifact.benchmarks.livebench_math.livebenchmath_utils.metric. "
                "Set GEPA_ARTIFACT_PATH to the path of the gepa-artifact repo. "
                "See tenants/livebench_math/docs/eval-operations.md."
            )
        if gepa_path not in sys.path:
            sys.path.insert(0, gepa_path)
        try:
            from gepa_artifact.benchmarks.livebench_math.livebenchmath_utils.metric import (  # noqa: PLC0415
                calculate_livebench_score,
            )
        except ImportError as exc:
            raise ImportError(
                f"Failed to import calculate_livebench_score from GEPA artifact at "
                f"{gepa_path}. Ensure the path is correct and the gepa env is installed. "
                f"Underlying error: {exc}"
            ) from exc
        _livebench_score_fn = calculate_livebench_score
        return _livebench_score_fn


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "answer" not in case.expected:
            raise ValueError(f"Case '{case.case_id}' missing expected.answer")
        if "question_d" not in case.metadata:
            raise ValueError(
                f"Case '{case.case_id}' missing metadata.question_d — required by "
                "calculate_livebench_score to dispatch on task type."
            )

    def score_case(
        self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        score_fn = _load_calculate_livebench_score()
        question_d = case.metadata["question_d"]
        try:
            raw, _feedback = score_fn(question_d, output_text, debug=False)
        except Exception:
            return {
                "composite_score": 0.0,
                "score_breakdown": {"livebench_score": 0.0, "scorer_ok": 0.0},
            }

        # ``calculate_livebench_score`` returns:
        #   - 0 or 1 for binary tasks (aime, amc, amps_hard, comparisons)
        #   - 0..100 for partial-credit proof-rearrangement (imo, usamo)
        score = float(raw)
        composite = score if score > 1.0 else score * 100.0
        composite = max(0.0, min(100.0, composite))
        return {
            "composite_score": composite,
            "score_breakdown": {"livebench_score": composite, "scorer_ok": 100.0},
        }

    def score_pipeline_case(
        self,
        case: EvalCase,
        step_outputs: Dict[str, str],
        scoring_profile: Dict[str, Any],
        output_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        if "solve" in step_outputs:
            final = step_outputs["solve"]
        elif output_text is not None:
            final = output_text
        elif step_outputs:
            final = list(step_outputs.values())[-1]
        else:
            raise ValueError("score_pipeline_case called with empty step_outputs and no output_text")
        return self.score_case(case, final, scoring_profile)
