# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import dataclasses
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Any, Dict, List

from src.hephaestus.chains.loader import load_chain_factory
from src.hephaestus.datasets.jsonl_loader import load_cases
from src.hephaestus.providers import build_provider_client
from src.hephaestus.providers.base import ProviderClient
from src.hephaestus.runs.io_utils import write_outputs
from src.hephaestus.runs.progress import ProgressTracker
from src.hephaestus.runs.run_id import generate_run_id, validate_run_id
from src.hephaestus.scoring.runtime import load_tenant_scorer, validate_score_payload
from src.hephaestus.scoring.scorer import Scorer
from src.hephaestus.types import ChainConfig, EvalCase, EvalCaseResult, EvalConfig

logger = logging.getLogger(__name__)

ALLOWED_PROVIDERS = {"baseten", "base10", "sagemaker", "openai"}


def load_eval_config(path: Path) -> EvalConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))

    if "chain" not in raw:
        raise ValueError("Config must specify 'chain'")

    chain_raw = raw["chain"]
    chain_path = chain_raw.get("path", "")
    if not chain_path:
        raise ValueError("Config missing chain.path")
    chain_config = ChainConfig(
        path=str(chain_path),
        fn=str(chain_raw.get("fn", "build_chain")),
        config=dict(chain_raw.get("config", {})),
    )

    dataset = raw.get("dataset", {})
    dataset_path = dataset.get("path")
    if not dataset_path:
        raise ValueError("Config missing dataset.path")

    provider = str(raw.get("provider", "")).strip().lower()
    if provider not in ALLOWED_PROVIDERS:
        raise ValueError(f"Unsupported provider '{provider}'. Supported: {sorted(ALLOWED_PROVIDERS)}")

    max_workers = raw.get("max_workers")
    if max_workers is not None:
        if not isinstance(max_workers, int) or isinstance(max_workers, bool) or max_workers < 1:
            raise ValueError(f"max_workers must be a positive integer, got {max_workers!r}")

    run_id = raw.get("run_id")
    if run_id is not None:
        run_id = str(run_id)
        validate_run_id(run_id)

    return EvalConfig(
        tenant_id=str(raw["tenant_id"]),
        provider=provider,
        provider_settings=dict(raw.get("provider_settings", {})),
        dataset_path=str(dataset_path),
        scoring_profile=dict(raw.get("scoring_profile", {})),
        output_dir=str(raw["output_dir"]),
        chain=chain_config,
        max_workers=max_workers,
        run_id=run_id,
    )


def _validate_eval_paths(config: EvalConfig) -> None:
    """Check that dataset, chain module, and prompt files exist before running."""
    dataset = Path(config.dataset_path)
    if not dataset.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset}. "
            "Run `python -m hephaestus.cli customer-data pull` to fetch datasets."
        )

    chain_path = Path(config.chain.path)
    if not chain_path.exists():
        raise FileNotFoundError(
            f"Chain module not found: {chain_path}. Check chain.path in your eval config."
        )

    for step_name, prompt_path_str in config.chain.config.get("prompt_paths", {}).items():
        prompt_path = Path(prompt_path_str)
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found for step '{step_name}': {prompt_path}. "
                "Check chain.config.prompt_paths in your eval config."
            )


def _ensure_chain(config: EvalConfig, provider: ProviderClient) -> Any:
    """Load a chain from the eval config."""
    factory = load_chain_factory(config.chain.path, config.chain.fn)
    return factory(provider, config.chain.config)


def _evaluate_single_case(
    case: EvalCase,
    chain: Any,
    scorer: Scorer,
    scoring_profile: Dict[str, Any],
    worker_index: int = 0,
) -> EvalCaseResult:
    """Run a single eval case through the chain and scorer.

    Thread-safety: this function is called concurrently when ``max_workers > 1``.
    ``chain`` and ``scorer`` must be safe to invoke from multiple threads
    (no mutable instance state).

    If the chain raises an exception, the case is scored with an empty output
    so that remaining cases can still be evaluated.
    """
    initial_state: Dict[str, Any] = {
        "context": copy.deepcopy(case.context),
        "output_text": "",
        "step_outputs": {},
        "diagnostics": [],
        "_worker_index": worker_index,
    }

    step_timings: List[List] = []
    final_state = dict(initial_state)
    chain_set_output_text = False

    try:
        t0 = time.monotonic()
        for chunk in chain.stream(initial_state):
            elapsed = time.monotonic() - t0
            for node_name in chunk:
                step_timings.append([node_name, round(elapsed, 3)])
                logger.info(
                    "case=%s step=%d node=%s elapsed=%.3fs",
                    case.case_id,
                    len(step_timings),
                    node_name,
                    elapsed,
                )
                if "output_text" in chunk[node_name]:
                    chain_set_output_text = True
                final_state.update(chunk[node_name])
            t0 = time.monotonic()
    except Exception as exc:
        logger.error(
            "Chain raised an exception for case %s: %s. "
            "Scoring with empty output.",
            case.case_id,
            exc,
        )
        final_state["diagnostics"] = [f"Chain exception: {exc}"]

    if not chain_set_output_text:
        logger.warning(
            "Chain for case %s did not produce 'output_text'; defaulting to empty string.",
            case.case_id,
        )
    output_text = final_state.get("output_text", "")
    step_outputs = final_state.get("step_outputs", {})

    score_payload = scorer.score_pipeline_case(
        case, step_outputs, scoring_profile, output_text=output_text,
    )

    composite_score, score_breakdown = validate_score_payload(score_payload)

    return EvalCaseResult(
        case_id=case.case_id,
        task_type=case.task_type,
        diagnostics=final_state.get("diagnostics", []),
        score_breakdown=score_breakdown,
        composite_score=composite_score,
        output_text=output_text,
        step_outputs=step_outputs,
        step_timings=step_timings,
    )


def _evaluate_and_track(
    case: EvalCase,
    chain: Any,
    scorer: Scorer,
    scoring_profile: Dict[str, Any],
    tracker: ProgressTracker,
    worker_index: int = 0,
) -> EvalCaseResult:
    """Run a single case and record progress."""
    tracker.record_start(case.case_id)
    result = _evaluate_single_case(case, chain, scorer, scoring_profile, worker_index=worker_index)
    tracker.record_result(result)
    return result


def run_evaluation(config: EvalConfig) -> List[Dict]:
    _validate_eval_paths(config)
    run_id = config.run_id or generate_run_id(config.tenant_id)

    cases = load_cases(Path(config.dataset_path))
    scorer = load_tenant_scorer(config.scoring_profile)
    for case in cases:
        scorer.validate_case(case, config.scoring_profile)

    provider = build_provider_client(config.provider, config.provider_settings)
    chain = _ensure_chain(config, provider)

    tracker = ProgressTracker(Path(config.output_dir), total_cases=len(cases), run_id=run_id)

    try:
        max_workers = config.max_workers
        if max_workers is not None and max_workers > 1:
            evaluate = partial(
                _evaluate_and_track,
                chain=chain, scorer=scorer,
                scoring_profile=config.scoring_profile, tracker=tracker,
            )
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx = {
                    executor.submit(evaluate, case, worker_index=i % max_workers): i
                    for i, case in enumerate(cases)
                }
                results: List[EvalCaseResult] = [None] * len(cases)  # type: ignore[list-item]
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    results[idx] = future.result()
        else:
            results = [
                _evaluate_and_track(case, chain, scorer, config.scoring_profile, tracker)
                for case in cases
            ]

        run_config: Dict[str, Any] = {
            "run_id": run_id,
            "tenant_id": config.tenant_id,
            "provider": config.provider,
            "provider_settings": config.provider_settings,
            "dataset_path": config.dataset_path,
            "scoring_profile": config.scoring_profile,
            "max_workers": max_workers,
            "chain": {
                "path": config.chain.path,
                "fn": config.chain.fn,
                "config": config.chain.config,
            },
        }
        result_dicts = [dataclasses.asdict(r) for r in results]
        write_outputs(Path(config.output_dir), run_config, result_dicts)

        # Mark completed only after outputs are successfully written
        tracker.mark_completed()

        return result_dicts
    except (Exception, KeyboardInterrupt, SystemExit):
        # Mark as failed if any exception or interruption occurs
        tracker.mark_failed()
        raise
