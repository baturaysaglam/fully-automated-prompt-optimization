#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build Hephaestus JSONL splits mirroring the GEPA paper's ``AIMEBench``.

Replicates :class:`gepa_artifact.benchmarks.AIME.AIME_data.AIMEBench` exactly:

1. Load ``AI-MO/aimo-validation-aime`` train (90 problems, 2022-2024 AIME).
2. Shuffle with ``random.Random(0)``.
3. Split 50/50: first half → train_set, second half → val_set.
4. Load ``MathArena/aime_2025`` train (30 problems) → test_set = (that list) * 5.
5. Apply ``trim_dataset(seed=1)`` with caps (150, 300, 300) — all splits fit
   below the caps so this is a no-op for AIME; produces 45 / 45 / 150.

Splits are committed to git (byte-level lock against GEPA). A fingerprint
written to ``splits.meta.json`` guards against future drift.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_OUTPUT_DIR = Path("tenants/aime/datasets/datasets")

# Caps from gepa_artifact.benchmarks.benchmark.Benchmark.__init__:
#   train cap = 150, val cap = 300, test cap = 300.
TRAIN_CAP = 150
VAL_CAP = 300
TEST_CAP = 300


def _trim(dataset: List[Any], size: int) -> List[Any]:
    """Mirror ``Benchmark.trim_dataset(dataset, size)`` with seed=1."""
    if size is None or size >= len(dataset):
        return dataset
    rng = random.Random()
    rng.seed(1)
    return rng.sample(dataset, size)


def _convert_train_val(raw: Dict[str, Any], split: str, idx: int) -> Dict[str, Any]:
    """Convert an AI-MO/aimo-validation-aime row to the Hephaestus EvalCase schema."""
    return {
        "case_id": f"aime-{split}-{idx}",
        "task_type": "math_cot",
        "context": {"problem": str(raw["problem"])},
        "expected": {
            "answer": str(raw["answer"]),
            "solution": str(raw.get("solution", "") or ""),
        },
        "metadata": {
            "source": "AI-MO/aimo-validation-aime",
            "split": split,
            "original_id": raw.get("id"),
            "url": raw.get("url", ""),
        },
    }


def _convert_test(raw: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Convert a MathArena/aime_2025 row to the Hephaestus EvalCase schema.

    The GEPA artifact replicates the test set 5x (``test_split * 5``). We
    preserve the original row's ``problem_idx`` under metadata so replicated
    copies are distinguishable in logs.
    """
    return {
        "case_id": f"aime-test-{idx}",
        "task_type": "math_cot",
        "context": {"problem": str(raw["problem"])},
        "expected": {"answer": str(raw["answer"]), "solution": ""},
        "metadata": {
            "source": "MathArena/aime_2025",
            "split": "test",
            "original_problem_idx": raw.get("problem_idx"),
            "problem_type": raw.get("problem_type"),
        },
    }


def _write_split(path: Path, cases: List[Dict[str, Any]]) -> None:
    """Write cases to JSONL, one per line, with sorted keys for determinism."""
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
    """Build train/val/test JSONL splits and write ``splits.meta.json``.

    Requires HuggingFace ``datasets`` with cached copies of
    ``AI-MO/aimo-validation-aime`` and ``MathArena/aime_2025``.
    """
    from datasets import load_dataset

    # --- Train/val: AI-MO/aimo-validation-aime, shuffled with seed=0, 50/50 split
    train_raw = list(load_dataset("AI-MO/aimo-validation-aime")["train"])
    random.Random(0).shuffle(train_raw)
    half = int(0.5 * len(train_raw))
    pre_train = train_raw[:half]
    pre_val = train_raw[half:]

    # --- Test: MathArena/aime_2025 * 5
    test_raw = list(load_dataset("MathArena/aime_2025")["train"])
    pre_test = test_raw * 5

    # --- Trim with seed=1 caps
    train = _trim(pre_train, TRAIN_CAP)
    val = _trim(pre_val, VAL_CAP)
    test = _trim(pre_test, TEST_CAP)

    train_cases = [_convert_train_val(r, "train", i) for i, r in enumerate(train)]
    val_cases = [_convert_train_val(r, "val", i) for i, r in enumerate(val)]
    test_cases = [_convert_test(r, i) for i, r in enumerate(test)]

    _write_split(output_dir / "train.jsonl", train_cases)
    _write_split(output_dir / "val.jsonl", val_cases)
    _write_split(output_dir / "test.jsonl", test_cases)

    gepa_path = Path(__file__).resolve().parents[4] / "gepa-artifact"
    meta = {
        "benchmark": "AIMEBench",
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
    parser = argparse.ArgumentParser(description="Build AIME dataset splits mirroring GEPA's AIMEBench.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    counts = build(args.output_dir)
    for name, n in counts.items():
        print(f"  {name}.jsonl: {n} cases")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
