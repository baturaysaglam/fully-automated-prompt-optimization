#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build Hephaestus JSONL splits mirroring GEPA's ``IFBench``.

Replicates :class:`gepa_artifact.benchmarks.IFBench.ifbench_data.IFBench`:

1. Load local JSONL files from the gepa-artifact repo:
   ``gepa_artifact/benchmarks/IFBench/data/IFBench_train.jsonl`` and
   ``IFBench_test.jsonl`` (set ``GEPA_ARTIFACT_PATH``).
2. Hardcoded sequential slices of the train file:
   - val = train_val[:300]
   - train = train_val[300:600]
   - test = all rows from ``IFBench_test.jsonl``
3. Apply ``trim_dataset(seed=1)`` with caps (150, 300, 300).

Post-trim sizes: 150 / 300 / 294 (test is below the cap; trim is a no-op).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_OUTPUT_DIR = Path("tenants/ifbench/datasets/datasets")

TRAIN_CAP = 150
VAL_CAP = 300
TEST_CAP = 300


def _trim(dataset: List[Any], size: int) -> List[Any]:
    if size is None or size >= len(dataset):
        return dataset
    rng = random.Random()
    rng.seed(1)
    return rng.sample(dataset, size)


def _convert(row: Dict[str, Any], split: str, idx: int) -> Dict[str, Any]:
    # IFBench rows carry: key, prompt, instruction_id (optional), kwargs, instruction_id_list
    # Keep the kwargs structure verbatim — the scorer passes it to
    # instruction.build_description(**kwargs[i]).
    return {
        "case_id": f"ifbench-{split}-{idx}",
        "task_type": "instruction_following",
        "context": {"prompt": str(row["prompt"])},
        "expected": {
            "instruction_id_list": list(row.get("instruction_id_list", [])),
            "kwargs": list(row.get("kwargs", [])),
            "key": row.get("key"),
        },
        "metadata": {
            "source": "IFBench",
            "split": split,
            "original_instruction_id": row.get("instruction_id"),
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
    gepa_path_str = os.environ.get("GEPA_ARTIFACT_PATH")
    if not gepa_path_str:
        raise RuntimeError(
            "GEPA_ARTIFACT_PATH is unset. IFBench data lives inside the gepa-artifact repo "
            "at gepa_artifact/benchmarks/IFBench/data/*.jsonl. Export GEPA_ARTIFACT_PATH "
            "to the path of that repo before running this builder."
        )
    gepa_path = Path(gepa_path_str)
    data_dir = gepa_path / "gepa_artifact" / "benchmarks" / "IFBench" / "data"
    train_path = data_dir / "IFBench_train.jsonl"
    test_path = data_dir / "IFBench_test.jsonl"

    with train_path.open(encoding="utf-8") as f:
        train_val = [json.loads(ln) for ln in f if ln.strip()]
    with test_path.open(encoding="utf-8") as f:
        test_raw = [json.loads(ln) for ln in f if ln.strip()]

    val_pre = train_val[:300]
    train_pre = train_val[300:600]
    test_pre = test_raw

    train = _trim(train_pre, TRAIN_CAP)
    val = _trim(val_pre, VAL_CAP)
    test = _trim(test_pre, TEST_CAP)

    train_cases = [_convert(row, "train", i) for i, row in enumerate(train)]
    val_cases = [_convert(row, "val", i) for i, row in enumerate(val)]
    test_cases = [_convert(row, "test", i) for i, row in enumerate(test)]

    _write_split(output_dir / "train.jsonl", train_cases)
    _write_split(output_dir / "val.jsonl", val_cases)
    _write_split(output_dir / "test.jsonl", test_cases)

    meta = {
        "benchmark": "IFBench",
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
    parser = argparse.ArgumentParser(description="Build IFBench dataset splits mirroring GEPA's IFBench.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    counts = build(args.output_dir)
    for name, n in counts.items():
        print(f"  {name}.jsonl: {n} cases")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
