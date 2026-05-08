# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""IFBench scorer wrapping GEPA's ``ifbench_metric.metric``.

GEPA's metric runs each listed instruction against 8 response variants
(original, the same without leading/trailing lines, and the same without
asterisks) and marks an instruction as satisfied if any variant passes.
Composite = ``mean(is_following) * 100``.

The scoring logic requires ``instructions_registry.INSTRUCTION_DICT`` from
the gepa-artifact repo, which in turn imports ``nltk``, ``spacy``, ``syllapy``,
``emoji``, and ``immutabledict``. We defer the import to
``score_case``-time and raise a clear ``ImportError`` that names the missing
deps and remediation if import fails.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import threading
from typing import Any, Dict, List, Optional

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase

_REQUIRED_DEPS = ("nltk", "spacy", "syllapy", "emoji", "immutabledict")

_instruction_dict: Optional[Dict[str, Any]] = None
_import_lock = threading.Lock()


def _missing_deps() -> List[str]:
    return [dep for dep in _REQUIRED_DEPS if importlib.util.find_spec(dep) is None]


def _load_instruction_dict() -> Dict[str, Any]:
    global _instruction_dict
    if _instruction_dict is not None:
        return _instruction_dict
    with _import_lock:
        if _instruction_dict is not None:
            return _instruction_dict

        gepa_path = os.environ.get("GEPA_ARTIFACT_PATH")
        if not gepa_path:
            raise ImportError(
                "GEPA_ARTIFACT_PATH is unset. The ifbench scorer wraps "
                "gepa_artifact.benchmarks.IFBench.utils_ifbench.instructions_registry. "
                "Set GEPA_ARTIFACT_PATH and ensure nltk/spacy/syllapy/emoji/immutabledict "
                "are installed in the Python env. See tenants/ifbench/docs/eval-operations.md."
            )
        missing = _missing_deps()
        if missing:
            raise ImportError(
                f"Missing deps required by ifbench scorer: {missing}. "
                "Install with: pip install " + " ".join(missing)
            )
        if gepa_path not in sys.path:
            sys.path.insert(0, gepa_path)
        try:
            from gepa_artifact.benchmarks.IFBench.utils_ifbench.instructions_registry import (  # noqa: PLC0415
                INSTRUCTION_DICT,
            )
        except ImportError as exc:
            raise ImportError(
                f"Failed to import instructions_registry from GEPA artifact at {gepa_path}: {exc}"
            ) from exc
        _instruction_dict = INSTRUCTION_DICT
        return _instruction_dict


def _evaluate_response(
    instruction_dict: Dict[str, Any],
    prompt: str,
    response: str,
    instruction_id_list: List[str],
    kwargs_list: List[Dict[str, Any]],
) -> List[bool]:
    """Port of ``ifbench_metric.metric_with_feedback``'s per-instruction check.

    For each instruction, tries the response plus 7 variants (drop-first-line,
    drop-last-line, drop-both, asterisk-stripped counterparts). An instruction
    is satisfied if any variant passes.
    """
    lines = response.split("\n")
    no_first = "\n".join(lines[1:]).strip()
    no_last = "\n".join(lines[:-1]).strip()
    no_both = "\n".join(lines[1:-1]).strip()
    variants = [
        response,
        response.replace("*", ""),
        no_first,
        no_last,
        no_both,
        no_first.replace("*", ""),
        no_last.replace("*", ""),
        no_both.replace("*", ""),
    ]

    is_following: List[bool] = []
    for index, instruction_id in enumerate(instruction_id_list):
        instruction_cls = instruction_dict[instruction_id]
        instruction = instruction_cls(instruction_id)
        if index < len(kwargs_list):
            kwargs = {k: v for k, v in kwargs_list[index].items() if v is not None}
        else:
            kwargs = {}
        instruction.build_description(**kwargs)
        args = instruction.get_instruction_args()
        if args and "prompt" in args:
            instruction.build_description(prompt=prompt)

        ok = False
        for variant in variants:
            if variant.strip() and instruction.check_following(variant):
                ok = True
                break
        is_following.append(ok)
    return is_following


class Scorer(BaseScorer):
    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        if "instruction_id_list" not in case.expected:
            raise ValueError(f"Case '{case.case_id}' missing expected.instruction_id_list")
        if not isinstance(case.expected["instruction_id_list"], list):
            raise ValueError(f"Case '{case.case_id}' expected.instruction_id_list must be a list")

    def score_case(
        self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        instruction_dict = _load_instruction_dict()
        instruction_id_list: List[str] = list(case.expected.get("instruction_id_list", []))
        kwargs_list: List[Dict[str, Any]] = list(case.expected.get("kwargs", []))
        prompt = case.context.get("prompt", "")

        if not instruction_id_list:
            return {
                "composite_score": 0.0,
                "score_breakdown": {"instruction_pass_rate": 0.0, "instructions_evaluated": 0.0},
            }

        try:
            is_following = _evaluate_response(
                instruction_dict, prompt, output_text, instruction_id_list, kwargs_list
            )
        except Exception:
            return {
                "composite_score": 0.0,
                "score_breakdown": {
                    "instruction_pass_rate": 0.0,
                    "instructions_evaluated": float(len(instruction_id_list)),
                    "scorer_ok": 0.0,
                },
            }

        pass_rate = 100.0 * sum(is_following) / len(is_following)
        return {
            "composite_score": pass_rate,
            "score_breakdown": {
                "instruction_pass_rate": pass_rate,
                "instructions_evaluated": float(len(is_following)),
                "scorer_ok": 100.0,
            },
        }

    def score_pipeline_case(
        self,
        case: EvalCase,
        step_outputs: Dict[str, str],
        scoring_profile: Dict[str, Any],
        output_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Use the final revision from ensure_correct_response if present, else fall back.
        if "ensure_correct_response" in step_outputs:
            final = step_outputs["ensure_correct_response"]
        elif output_text is not None:
            final = output_text
        elif step_outputs:
            final = list(step_outputs.values())[-1]
        else:
            raise ValueError("score_pipeline_case called with empty step_outputs and no output_text")
        return self.score_case(case, final, scoring_profile)


# Injection hook for unit tests: pytest monkeypatch can set the cached
# instruction dict here so scoring runs without needing the real gepa-artifact.
def _set_instruction_dict_for_testing(d: Optional[Dict[str, Any]]) -> None:
    global _instruction_dict
    _instruction_dict = d
