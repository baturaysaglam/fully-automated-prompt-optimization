# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""End-to-end integration smoke test for the Hephaestus eval pipeline.

Exercises: GCS data pull, eval with a bad prompt (expect failure),
eval with a good prompt (expect pass), and verifies improvement.

Requires:
  - OPENAI_API_KEY env var set
  - GCS access for pulling the smoke_test tenant dataset

Run with:  pytest -m integration -v
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.hephaestus.runs.eval_runner import run_evaluation
from src.hephaestus.storage.config import TenantStorageConfig, load_storage_config
from src.hephaestus.storage.gcs_sync import pull_customer_data
from src.hephaestus.types import ChainConfig, EvalConfig

pytestmark = pytest.mark.integration

TENANT_ID = "smoke_test"
HEPH_ROOT = Path(__file__).resolve().parent.parent
TENANT_ROOT = HEPH_ROOT / "tenants" / TENANT_ID
STORAGE_CONFIG_PATH = TENANT_ROOT / "storage" / "config.json"

CHAIN_PATH = TENANT_ROOT / "chains" / "answer.py"
SCORER_PATH = TENANT_ROOT / "code" / "scorers" / "exact_match.py"
VARIANT_001 = TENANT_ROOT / "prompts" / "variants" / "variant-001.md"
VARIANT_002 = TENANT_ROOT / "prompts" / "variants" / "variant-002.md"

PASS_THRESHOLD = 80.0


def _skip_if_no_openai_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")


def _load_storage():
    """Load storage config using an absolute path so the test works from any cwd."""
    return load_storage_config(TENANT_ID, path=STORAGE_CONFIG_PATH)


def _dataset_path(storage_config: TenantStorageConfig) -> Path:
    """Derive the dataset path from the storage config's derived_local field."""
    return HEPH_ROOT / storage_config.derived_local / "datasets" / "cases.jsonl"


def _build_eval_config(
    prompt_path: Path,
    output_dir: Path,
    dataset_path: Path,
    max_workers: int | None = None,
) -> EvalConfig:
    return EvalConfig(
        tenant_id=TENANT_ID,
        provider="openai",
        provider_settings={
            "model": "gpt-4o-mini",
            "temperature": 0.0,
            "max_tokens": 16,
        },
        dataset_path=str(dataset_path),
        scoring_profile={
            "scorer": {"module_path": str(SCORER_PATH)},
        },
        output_dir=str(output_dir),
        chain=ChainConfig(
            path=str(CHAIN_PATH),
            fn="build_chain",
            config={"prompt_paths": {"answer": str(prompt_path)}},
        ),
        max_workers=max_workers,
    )


def _avg_composite(results: List[Dict[str, Any]]) -> float:
    scores = [r["composite_score"] for r in results]
    return sum(scores) / len(scores)


@pytest.fixture(scope="class")
def smoke_dataset_path():
    """Pull the smoke_test dataset once for all tests in the class."""
    _skip_if_no_openai_key()
    storage_config = _load_storage()
    pull_customer_data(storage_config, scope="derived")
    ds_path = _dataset_path(storage_config)
    assert ds_path.exists(), f"Dataset not found after pull: {ds_path}"
    return ds_path


class TestSmokeFullWorkflow:
    """Full pipeline smoke test: pull data, eval bad prompt, eval good prompt."""

    def test_smoke_full_workflow(self, tmp_path: Path, smoke_dataset_path: Path) -> None:
        ds_path = smoke_dataset_path

        # Step 1: Eval with bad prompt (variant-001, verbose answers)
        bad_results = run_evaluation(
            _build_eval_config(VARIANT_001, tmp_path / "eval-bad", ds_path)
        )
        bad_avg = _avg_composite(bad_results)
        assert bad_avg < PASS_THRESHOLD, (
            f"Bad prompt should fail (avg {bad_avg:.1f} >= {PASS_THRESHOLD})"
        )

        # Step 2: Eval with good prompt (variant-002, strict yes/no)
        good_results = run_evaluation(
            _build_eval_config(VARIANT_002, tmp_path / "eval-good", ds_path)
        )
        good_avg = _avg_composite(good_results)
        assert good_avg >= PASS_THRESHOLD, (
            f"Good prompt should pass (avg {good_avg:.1f} < {PASS_THRESHOLD})"
        )

        # Step 3: Improvement
        assert good_avg > bad_avg, (
            f"Good prompt ({good_avg:.1f}) should beat bad prompt ({bad_avg:.1f})"
        )

    def test_smoke_concurrent_passes_threshold(
        self, tmp_path: Path, smoke_dataset_path: Path,
    ) -> None:
        """Verify concurrent eval (max_workers=2) passes the score threshold."""
        ds_path = smoke_dataset_path

        results = run_evaluation(
            _build_eval_config(
                VARIANT_002, tmp_path / "eval-conc", ds_path, max_workers=2,
            )
        )

        assert len(results) > 0, "Concurrent run produced no results"
        avg = _avg_composite(results)
        assert avg >= PASS_THRESHOLD, (
            f"Concurrent run should pass (avg {avg:.1f} < {PASS_THRESHOLD})"
        )
