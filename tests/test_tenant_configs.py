# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests verifying committed tenant chain configs load and run correctly.

Loads the committed hotpotqa chain config and runs evaluation with a mocked
provider to validate the config structure and scoring pipeline.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from helpers import TrackingProvider

import src.hephaestus.runs.eval_runner as eval_runner
from src.hephaestus.runs.eval_runner import load_eval_config, run_evaluation

# ---------------------------------------------------------------------------
# Committed tenant chain config tests
# ---------------------------------------------------------------------------

# Canned response for hotpotqa — a simple answer string that the scorer can
# normalise and compare against the expected answer.
_HOTPOTQA_CANNED = "Yes"
_HOTPOTQA_CANNED_PASSAGES = ["Passage 1.", "Passage 2."]

_COMMITTED_CHAIN_CONFIGS = [
    pytest.param(
        "tenants/hotpotqa/configs/local-chain-variant001.json",
        _HOTPOTQA_CANNED,
        id="hotpotqa",
    ),
]


@pytest.mark.parametrize("config_rel_path,canned_response", _COMMITTED_CHAIN_CONFIGS)
def test_committed_chain_config_loads_and_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_rel_path: str,
    canned_response: str,
) -> None:
    """Committed tenant chain configs load and run successfully with mocked provider."""
    config_path = Path(config_rel_path)
    if not config_path.exists():
        pytest.skip(f"Config not found: {config_rel_path}")

    loaded = load_eval_config(config_path)

    # Skip if tenant dataset is not present (local artifact, not tracked in git)
    if not Path(loaded.dataset_path).exists():
        pytest.skip(f"Dataset not found: {loaded.dataset_path}")

    # Redirect output_dir to tmp_path so we don't pollute the repo
    loaded.output_dir = str(tmp_path / "eval_output")

    # Count cases so we supply enough canned responses
    case_count = sum(1 for _ in open(loaded.dataset_path, encoding="utf-8") if _.strip())

    provider = TrackingProvider([canned_response] * case_count)
    monkeypatch.setattr(
        eval_runner, "build_provider_client", lambda _p, _s: provider
    )

    # Mock BM25 retrieval so we don't need a built index (hotpotqa)
    if "hotpotqa" in config_rel_path:
        import tenants.hotpotqa.code.retrieval as _retrieval_mod

        monkeypatch.setattr(
            _retrieval_mod,
            "_search_bm25",
            lambda query, k, data_dir: _HOTPOTQA_CANNED_PASSAGES,
        )

    results = run_evaluation(loaded)

    assert len(results) == case_count
    for r in results:
        assert "case_id" in r
        assert "composite_score" in r
        assert isinstance(r["composite_score"], (int, float))
        assert "score_breakdown" in r
        assert isinstance(r["score_breakdown"], dict)
        assert "output_text" in r
        assert "step_outputs" in r  # chain mode always includes step_outputs
