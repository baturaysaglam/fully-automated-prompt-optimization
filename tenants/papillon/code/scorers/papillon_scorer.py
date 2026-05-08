# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Papillon scorer mirroring GEPA's ``compute_overall_score``.

GEPA's metric is:

    overall = (quality + (1 - leakage)) / 2

where
  - ``quality`` is a binary LLM-judge comparison between the model's final
    response and the gold ``target_response``.
  - ``leakage`` is a fraction in [0, 1] representing the rate at which PII
    units from ``expected.pii_units`` appear in the redacted request.

The FEPO scorer splits these into two paths:

  - **Leakage path** (pure, no LLM): deterministic containment check,
    fully unit-testable without ``OPENAI_API_KEY``.
  - **Quality path** (LLM-judge): makes an extra ``provider.generate`` call
    against a judge prompt. Can be stubbed in unit tests via the
    ``quality_fn`` parameter.

Composite = ``100 * (quality + (1 - leakage)) / 2`` (range ``[0, 100]``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from src.hephaestus.scoring.scorer import Scorer as BaseScorer
from src.hephaestus.types import EvalCase


def compute_leakage_rate(redacted_request: str, pii_units: Iterable[str]) -> float:
    """Fraction of PII units that appear literally in the redacted request.

    Returns 0.0 when there are no PII units (avoids division-by-zero; matches
    GEPA's guard in ``LLMJudge.forward``).
    """
    units = [u for u in pii_units if u]
    if not units:
        return 0.0
    hits = sum(1 for u in units if u in redacted_request)
    return hits / len(units)


def default_quality_fn(
    provider: Any,
    user_query: str,
    target_response: str,
    model_response: str,
    judge_prompt_path: Optional[Path],
) -> float:
    """Default quality judge: asks the provider to compare responses.

    Returns 1.0 if judge says "YES" (i.e., model response is at least as good
    as gold), 0.0 otherwise. Uses ``judge_prompt_path`` if supplied; else a
    built-in prompt modelled on GEPA's ``JudgeQuality`` signature.
    """
    if judge_prompt_path is not None:
        template = judge_prompt_path.read_text(encoding="utf-8")
        # Simple $-substitution (no complex rendering needed).
        prompt_text = (
            template.replace("${user_query}", user_query)
            .replace("${target_response}", target_response)
            .replace("${model_response}", model_response)
        )
    else:
        prompt_text = (
            "You are comparing the quality of two responses, given a user query. "
            "Is response A at least as good as response B? Reply with only YES or NO.\n\n"
            f"User query: {user_query}\n\n"
            f"Response A (model): {model_response}\n\n"
            f"Response B (gold target): {target_response}"
        )
    raw = provider.generate([{"role": "system", "content": prompt_text}])
    return 1.0 if raw.strip().upper().startswith("YES") else 0.0


class Scorer(BaseScorer):
    """Papillon scorer.

    Parameters for ``score_case`` via ``scoring_profile['tenant_config']``:
      - ``judge_prompt_path``: optional path to a judge prompt template
        (rendered with ``${user_query}``, ``${target_response}``,
        ``${model_response}``). Defaults to a built-in prompt.
      - ``judge_provider``: optional dict with ``{'provider': ..., 'settings': ...}``
        for a dedicated judge LM; if absent, the leakage-only path is used
        and ``quality`` is not computed (scoring defaults to quality=0.0).
      - ``quality_fn``: optional Python callable for tests. If provided,
        bypasses the LLM judge.
    """

    def validate_case(self, case: EvalCase, scoring_profile: Dict[str, Any]) -> None:
        for key in ("target_response", "pii_units"):
            if key not in case.expected:
                raise ValueError(f"Case '{case.case_id}' missing expected.{key}")
        if not isinstance(case.expected["pii_units"], list):
            raise ValueError(f"Case '{case.case_id}' expected.pii_units must be a list")

    def score_case(
        self, case: EvalCase, output_text: str, scoring_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        # score_case is a fallback when step_outputs is empty; compute leakage
        # against output_text (limited signal) and skip the quality judge.
        pii_units: List[str] = list(case.expected.get("pii_units", []))
        leakage_rate = compute_leakage_rate(output_text, pii_units)
        composite = 100.0 * (0.0 + (1.0 - leakage_rate)) / 2.0
        return {
            "composite_score": composite,
            "score_breakdown": {
                "quality": 0.0,
                "leakage_rate": leakage_rate,
                "composite": composite,
            },
        }

    def score_pipeline_case(
        self,
        case: EvalCase,
        step_outputs: Dict[str, str],
        scoring_profile: Dict[str, Any],
        output_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        pii_units: List[str] = list(case.expected.get("pii_units", []))
        redacted = step_outputs.get("craft_redacted_request", "")
        final_response = (
            step_outputs.get("respond_to_query")
            or output_text
            or (list(step_outputs.values())[-1] if step_outputs else "")
        )

        leakage_rate = compute_leakage_rate(redacted, pii_units)

        tenant_cfg: Dict[str, Any] = scoring_profile.get("tenant_config", {}) or {}
        quality_fn: Optional[Callable] = tenant_cfg.get("quality_fn")
        quality: float = 0.0

        if quality_fn is not None:
            quality = float(
                quality_fn(
                    user_query=case.context.get("user_query", ""),
                    target_response=case.expected.get("target_response", ""),
                    model_response=final_response,
                )
            )
        elif tenant_cfg.get("judge_provider"):
            # LLM-judge path — lazy-imported to avoid pulling provider deps
            # into unit tests that only exercise leakage.
            from src.hephaestus.providers import build_provider_client  # noqa: PLC0415

            judge_cfg = tenant_cfg["judge_provider"]
            provider = build_provider_client(
                judge_cfg.get("provider", "openai"),
                judge_cfg.get("settings", {"model": "gpt-4.1-mini", "temperature": 0.0, "max_tokens": 16}),
            )
            judge_prompt_path = tenant_cfg.get("judge_prompt_path")
            quality = default_quality_fn(
                provider,
                case.context.get("user_query", ""),
                case.expected.get("target_response", ""),
                final_response,
                Path(judge_prompt_path) if judge_prompt_path else None,
            )

        composite = 100.0 * (quality + (1.0 - leakage_rate)) / 2.0
        return {
            "composite_score": composite,
            "score_breakdown": {
                "quality": 100.0 * quality,
                "leakage_rate": leakage_rate,
                "composite": composite,
            },
        }
