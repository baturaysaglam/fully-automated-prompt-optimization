#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build Hephaestus JSONL splits from HuggingFace HotpotQA fullwiki.

Replicates the GEPA paper's Benchmark.create_splits() so that our
train/val/test splits match exactly:

1. Load ALL ``hotpot_qa`` ``fullwiki`` train examples (no difficulty filter).
2. Split sequentially: first 40% → test_pool, next 40% → val_pool,
   last 20% → train_pool.
3. Sub-sample each pool with ``random.Random(1).sample()`` to produce final
   splits (seed=1 for all, matching GEPA's ``trim_dataset``).
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_DIR = Path("tenants/hotpotqa/datasets/datasets")

# DSPy defaults
DEFAULT_TRAIN_SIZE = 150
DEFAULT_VAL_SIZE = 300
DEFAULT_TEST_SIZE = 300
DEFAULT_TRAIN_SEED = 1
DEFAULT_EVAL_SEED = 1


def _convert_case(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert a single HuggingFace fullwiki example to Hephaestus format.

    HuggingFace ``hotpot_qa`` ``fullwiki`` stores ``supporting_facts`` as a
    dict with parallel lists (``{"title": [...], "sent_id": [...]}``).  We
    convert this to the canonical list-of-pairs format used elsewhere in the
    Hephaestus pipeline.
    """
    sf = raw["supporting_facts"]
    if isinstance(sf, dict):
        supporting_facts = list(zip(sf["title"], sf["sent_id"]))
    else:
        supporting_facts = sf

    return {
        "case_id": str(raw["id"]),
        "task_type": "multihop_qa",
        "context": {"question": raw["question"]},
        "expected": {
            "answer": raw["answer"],
            "answer_type": raw["type"],
            "supporting_facts": supporting_facts,
        },
        "metadata": {
            "level": raw["level"],
            "source": "hotpotqa-fullwiki",
        },
    }


def _sample(
    pool: list[dict[str, Any]],
    seed: int,
    n: int,
) -> list[dict[str, Any]]:
    """Return *n* items sampled from *pool* using ``random.Random(seed).sample()``.

    Matches GEPA's ``Benchmark.trim_dataset`` which uses ``rng.sample(dataset, size)``.
    """
    if n >= len(pool):
        return list(pool)
    rng = random.Random()
    rng.seed(seed)
    return rng.sample(pool, n)


def _load_fullwiki_pools() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Load HuggingFace fullwiki data and return (train_pool, val_pool, test_pool).

    Follows GEPA's ``Benchmark.create_splits()``:
    - Load ALL HF train examples (no difficulty filter).
    - Split sequentially: first 40% → test, next 40% → val, last 20% → train.
    """
    from datasets import load_dataset

    dataset = list(load_dataset("hotpot_qa", "fullwiki", split="train"))

    total_len = len(dataset)
    test_pool = dataset[: int(0.4 * total_len)]
    val_pool = dataset[int(0.4 * total_len) : int(0.8 * total_len)]
    train_pool = dataset[int(0.8 * total_len) :]

    return train_pool, val_pool, test_pool


def build_splits(
    train_pool: list[dict[str, Any]],
    val_pool: list[dict[str, Any]],
    test_pool: list[dict[str, Any]],
    output_dir: Path,
    *,
    train_size: int = DEFAULT_TRAIN_SIZE,
    val_size: int = DEFAULT_VAL_SIZE,
    test_size: int = DEFAULT_TEST_SIZE,
    train_seed: int = DEFAULT_TRAIN_SEED,
    eval_seed: int = DEFAULT_EVAL_SEED,
) -> dict[str, int]:
    """Sub-sample pools and write train/val/test JSONL files.

    Returns a dict mapping split name to the number of cases written.
    """
    splits = {
        "train": _sample(train_pool, train_seed, train_size),
        "val": _sample(val_pool, eval_seed, val_size),
        "test": _sample(test_pool, eval_seed, test_size),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for name, cases in splits.items():
        path = output_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for raw in cases:
                f.write(json.dumps(_convert_case(raw)))
                f.write("\n")
        counts[name] = len(cases)

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Hephaestus JSONL splits from HuggingFace HotpotQA fullwiki.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write train.jsonl / val.jsonl / test.jsonl",
    )
    parser.add_argument(
        "--train-size",
        type=int,
        default=DEFAULT_TRAIN_SIZE,
        help="Number of training examples (default: 150)",
    )
    parser.add_argument(
        "--val-size",
        type=int,
        default=DEFAULT_VAL_SIZE,
        help="Number of validation examples (default: 300)",
    )
    parser.add_argument(
        "--test-size",
        type=int,
        default=DEFAULT_TEST_SIZE,
        help="Number of test examples (default: 300)",
    )
    parser.add_argument(
        "--train-seed",
        type=int,
        default=DEFAULT_TRAIN_SEED,
        help="Seed for shuffling train pool (default: 1)",
    )
    parser.add_argument(
        "--eval-seed",
        type=int,
        default=DEFAULT_EVAL_SEED,
        help="Seed for sampling val/test pools (default: 1)",
    )
    args = parser.parse_args()

    print("Loading HotpotQA fullwiki from HuggingFace...")
    train_pool, val_pool, test_pool = _load_fullwiki_pools()
    print(
        f"Pools: train={len(train_pool)}, val={len(val_pool)}, test={len(test_pool)}"
    )

    counts = build_splits(
        train_pool,
        val_pool,
        test_pool,
        args.output_dir,
        train_size=args.train_size,
        val_size=args.val_size,
        test_size=args.test_size,
        train_seed=args.train_seed,
        eval_seed=args.eval_seed,
    )
    for name, n in counts.items():
        print(f"  {name}.jsonl: {n} cases")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
