# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from src.hephaestus.datasets.jsonl_loader import load_cases
from tenants.hotpotqa.code.build_cases_jsonl import (
    _convert_case,
    build_splits,
)


def _make_fullwiki_cases(n: int = 3, *, level: str = "hard") -> list[dict]:
    """Create fake HuggingFace fullwiki-format HotpotQA cases."""
    cases = []
    for i in range(n):
        cases.append(
            {
                "id": f"test-{i:03d}",
                "question": f"Question number {i}?",
                "answer": f"answer-{i}",
                "type": "bridge" if i % 2 == 0 else "comparison",
                "level": level,
                "supporting_facts": {
                    "title": ["Title A", "Title B"],
                    "sent_id": [0, 1],
                },
                "context": {
                    "title": ["Title A", "Title B"],
                    "sentences": [
                        ["Sentence 0.", "Sentence 1."],
                        ["Sentence 0.", "Sentence 1."],
                    ],
                },
            }
        )
    return cases


# --- _convert_case handles fullwiki format ---


def test_convert_case_fullwiki_format() -> None:
    """_convert_case should convert HF fullwiki dict-style supporting_facts."""
    raw = _make_fullwiki_cases(1)[0]
    case = _convert_case(raw)

    assert case["case_id"] == "test-000"
    assert case["task_type"] == "multihop_qa"
    assert case["context"]["question"] == "Question number 0?"
    assert case["expected"]["answer"] == "answer-0"
    assert case["expected"]["answer_type"] == "bridge"
    assert case["expected"]["supporting_facts"] == [("Title A", 0), ("Title B", 1)]
    assert case["metadata"]["level"] == "hard"
    assert case["metadata"]["source"] == "hotpotqa-fullwiki"


def test_convert_case_list_style_supporting_facts() -> None:
    """_convert_case should also accept list-of-pairs supporting_facts."""
    raw = _make_fullwiki_cases(1)[0]
    raw["supporting_facts"] = [["Title A", 0], ["Title B", 1]]
    case = _convert_case(raw)
    assert case["expected"]["supporting_facts"] == [["Title A", 0], ["Title B", 1]]


# --- build_splits produces 3 JSONL files ---


def test_build_splits_produces_three_files(tmp_path: Path) -> None:
    """build_splits should create train.jsonl, val.jsonl, test.jsonl."""
    train_pool = _make_fullwiki_cases(20)
    dev_pool = _make_fullwiki_cases(20)
    test_pool = _make_fullwiki_cases(20)

    counts = build_splits(
        train_pool,
        dev_pool,
        test_pool,
        tmp_path,
        train_size=5,
        val_size=10,
        test_size=10,
    )

    assert counts == {"train": 5, "val": 10, "test": 10}
    assert (tmp_path / "train.jsonl").exists()
    assert (tmp_path / "val.jsonl").exists()
    assert (tmp_path / "test.jsonl").exists()


def test_build_splits_correct_sizes(tmp_path: Path) -> None:
    """Each output file should have the requested number of cases."""
    train_pool = _make_fullwiki_cases(50)
    dev_pool = _make_fullwiki_cases(50)
    test_pool = _make_fullwiki_cases(50)

    build_splits(
        train_pool,
        dev_pool,
        test_pool,
        tmp_path,
        train_size=10,
        val_size=20,
        test_size=15,
    )

    assert len(load_cases(tmp_path / "train.jsonl")) == 10
    assert len(load_cases(tmp_path / "val.jsonl")) == 20
    assert len(load_cases(tmp_path / "test.jsonl")) == 15


def test_build_splits_valid_eval_cases(tmp_path: Path) -> None:
    """Output JSONL should load as valid EvalCases."""
    pool = _make_fullwiki_cases(10)

    build_splits(pool, pool, pool, tmp_path, train_size=3, val_size=3, test_size=3)

    cases = load_cases(tmp_path / "train.jsonl")
    assert len(cases) == 3
    case = cases[0]
    assert case.task_type == "multihop_qa"
    assert "question" in case.context
    assert "answer" in case.expected
    assert case.metadata["source"] == "hotpotqa-fullwiki"


def test_build_splits_deterministic(tmp_path: Path) -> None:
    """Same seeds should produce identical output files."""
    pool = _make_fullwiki_cases(30)
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"

    for d in (dir_a, dir_b):
        build_splits(
            pool,
            pool,
            pool,
            d,
            train_size=5,
            val_size=10,
            test_size=10,
            train_seed=42,
            eval_seed=99,
        )

    for name in ("train.jsonl", "val.jsonl", "test.jsonl"):
        assert (dir_a / name).read_text() == (dir_b / name).read_text()


def test_build_splits_different_seeds_differ(tmp_path: Path) -> None:
    """Different seeds should produce different output."""
    pool = _make_fullwiki_cases(30)
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"

    build_splits(
        pool, pool, pool, dir_a, train_size=10, val_size=10, test_size=10, train_seed=1
    )
    build_splits(
        pool, pool, pool, dir_b, train_size=10, val_size=10, test_size=10, train_seed=2
    )

    assert (dir_a / "train.jsonl").read_text() != (dir_b / "train.jsonl").read_text()


def test_build_splits_creates_output_directory(tmp_path: Path) -> None:
    """Output directory should be created if it doesn't exist."""
    pool = _make_fullwiki_cases(5)
    output_dir = tmp_path / "nested" / "dir"

    build_splits(pool, pool, pool, output_dir, train_size=2, val_size=2, test_size=2)

    assert output_dir.exists()
    assert len(load_cases(output_dir / "train.jsonl")) == 2


def test_build_splits_caps_at_pool_size(tmp_path: Path) -> None:
    """If requested size exceeds pool, output should be capped at pool size."""
    pool = _make_fullwiki_cases(5)

    counts = build_splits(
        pool, pool, pool, tmp_path, train_size=100, val_size=100, test_size=100
    )

    assert counts["train"] == 5
    assert counts["val"] == 5
    assert counts["test"] == 5
