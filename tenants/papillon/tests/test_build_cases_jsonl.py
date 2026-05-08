# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests that committed papillon dataset files load and match their fingerprint."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.hephaestus.datasets.jsonl_loader import load_cases

DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets" / "datasets"
EXPECTED_SIZES = {"train": 111, "val": 111, "test": 221}


pytestmark = pytest.mark.requires_local_datasets


@pytest.mark.parametrize("split,expected", list(EXPECTED_SIZES.items()))
def test_split_size_matches(split: str, expected: int) -> None:
    path = DATASET_DIR / f"{split}.jsonl"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == expected


@pytest.mark.parametrize("split", ["train", "val", "test"])
def test_split_loads_as_eval_cases(split: str) -> None:
    cases = load_cases(DATASET_DIR / f"{split}.jsonl")
    for case in cases:
        assert case.task_type == "privacy_utility"
        assert "user_query" in case.context
        assert "target_response" in case.expected
        assert "pii_units" in case.expected
        assert isinstance(case.expected["pii_units"], list)


def test_fingerprint_matches_meta() -> None:
    meta = json.loads((DATASET_DIR / "splits.meta.json").read_text(encoding="utf-8"))
    h = hashlib.sha256()
    for name in ("train", "val", "test"):
        h.update((DATASET_DIR / f"{name}.jsonl").read_bytes())
    assert h.hexdigest() == meta["fingerprint_sha256"]


def test_meta_sizes_match_expectations() -> None:
    meta = json.loads((DATASET_DIR / "splits.meta.json").read_text(encoding="utf-8"))
    assert meta["train_size"] == EXPECTED_SIZES["train"]
    assert meta["val_size"] == EXPECTED_SIZES["val"]
    assert meta["test_size"] == EXPECTED_SIZES["test"]
