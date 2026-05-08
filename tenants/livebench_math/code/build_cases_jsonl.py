#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build Hephaestus JSONL splits mirroring GEPA's ``LiveBenchMathBench``.

Replicates :class:`gepa_artifact.benchmarks.livebench_math.livebenchmath_data.LiveBenchMathBench`:

1. Load ``livebench/math`` test split (368 rows in the cached version at time of writing).
2. Shuffle with ``random.Random(0)``.
3. Sequential split: train = first 33%, val = middle 33%, test = last 34%.
4. Apply ``trim_dataset(seed=1)`` with caps (150, 300, 300) — a no-op here
   because each subset is well under the cap.

Splits are committed to git for byte-level lock with GEPA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_OUTPUT_DIR = Path("tenants/livebench_math/datasets/datasets")

TRAIN_CAP = 150
VAL_CAP = 300
TEST_CAP = 300


def _trim(dataset: List[Any], size: int) -> List[Any]:
    if size is None or size >= len(dataset):
        return dataset
    rng = random.Random()
    rng.seed(1)
    return rng.sample(dataset, size)


def _to_jsonable(value: Any) -> Any:
    """Recursively convert HF rows (may include numpy types, dates) to JSON-safe values."""
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _convert(example: Dict[str, Any], split: str, idx: int) -> Dict[str, Any]:
    # GEPA's program uses: context={question: turns[0]}, expected={answer: ground_truth}.
    turns = example.get("turns") or []
    question = str(turns[0]) if turns else ""
    return {
        "case_id": f"livebench-math-{split}-{idx}",
        "task_type": "livebench_math_cot",
        "context": {"question": question},
        "expected": {"answer": str(example.get("ground_truth", ""))},
        "metadata": {
            "source": "livebench/math",
            "split": split,
            "original_question_id": example.get("question_id"),
            "category": example.get("category"),
            "task": example.get("task"),
            "subtask": example.get("subtask"),
            # Preserve the full example (JSON-safe) as ``question_d`` — the scorer
            # passes this verbatim to ``calculate_livebench_score``.
            "question_d": _to_jsonable(example),
        },
    }


def _write_split(path: Path, cases: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, sort_keys=True))
            f.write("\n")


def _fingerprint(output_dir: Path) -> str:
    h = hashlib.sha256()
    for name in ("train", "val", "test"):
        h.update((output_dir / f"{name}.jsonl").read_bytes())
    return h.hexdigest()


def _gepa_artifact_sha(gepa_path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(gepa_path), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


def build(output_dir: Path) -> Dict[str, int]:
    from datasets import load_dataset

    raw = list(load_dataset("livebench/math")["test"])
    # Convert each HF row to a plain JSON-safe dict eagerly so downstream
    # shuffling and indexing are stable.
    rows = [_to_jsonable(r) for r in raw]
    tot = len(rows)

    random.Random(0).shuffle(rows)

    pre_train = rows[: int(tot * 0.33)]
    pre_val = rows[int(tot * 0.33) : int(tot * 0.66)]
    pre_test = rows[int(tot * 0.66) :]

    train = _trim(pre_train, TRAIN_CAP)
    val = _trim(pre_val, VAL_CAP)
    test = _trim(pre_test, TEST_CAP)

    train_cases = [_convert(ex, "train", i) for i, ex in enumerate(train)]
    val_cases = [_convert(ex, "val", i) for i, ex in enumerate(val)]
    test_cases = [_convert(ex, "test", i) for i, ex in enumerate(test)]

    _write_split(output_dir / "train.jsonl", train_cases)
    _write_split(output_dir / "val.jsonl", val_cases)
    _write_split(output_dir / "test.jsonl", test_cases)

    gepa_path = Path(__file__).resolve().parents[4] / "gepa-artifact"
    meta = {
        "benchmark": "LiveBenchMathBench",
        "gepa_artifact_git_sha": _gepa_artifact_sha(gepa_path),
        "dataset_mode": "lite",
        "train_size": len(train_cases),
        "val_size": len(val_cases),
        "test_size": len(test_cases),
        "fingerprint_sha256": _fingerprint(output_dir),
    }
    (output_dir / "splits.meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"train": len(train_cases), "val": len(val_cases), "test": len(test_cases)}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build LiveBench-Math dataset splits mirroring GEPA's LiveBenchMathBench.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    counts = build(args.output_dir)
    for name, n in counts.items():
        print(f"  {name}.jsonl: {n} cases")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
