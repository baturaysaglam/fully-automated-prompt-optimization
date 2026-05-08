#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build Hephaestus JSONL splits mirroring the GEPA paper's ``hoverBench``.

Replicates :class:`gepa_artifact.benchmarks.hover.hover_data.hoverBench` exactly:

1. Load HuggingFace ``hover`` train split (18171 examples).
2. Filter to examples with exactly 3 unique supporting-fact documents
   (GEPA's ``count_unique_docs(example) == 3`` at ``hover_utils.py:3``).
3. Shuffle with ``random.Random(0)``.
4. Apply base ``create_splits()``: sequential 40/40/20 split → test_pool / val_pool / train_pool.
5. Apply ``trim_dataset(seed=1)``: 150 train / 300 val / 300 test.

Splits are committed to git for byte-level lock with GEPA. A fingerprint
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

DEFAULT_OUTPUT_DIR = Path("tenants/hover/datasets/datasets")

TRAIN_CAP = 150
VAL_CAP = 300
TEST_CAP = 300


def _count_unique_docs(example: Dict[str, Any]) -> int:
    """Mirror ``gepa_artifact.benchmarks.hover.hover_utils.count_unique_docs``."""
    return len({fact["key"] for fact in example["supporting_facts"]})


def _trim(dataset: List[Any], size: int) -> List[Any]:
    if size is None or size >= len(dataset):
        return dataset
    rng = random.Random()
    rng.seed(1)
    return rng.sample(dataset, size)


def _label_name(label: Any) -> str:
    # HoVer label encoding: HF's ClassLabel uses {0: 'SUPPORTED', 1: 'NOT_SUPPORTED'}.
    # GEPA keeps the integer verbatim; we expose both for downstream flexibility.
    if isinstance(label, str):
        return label
    mapping = {0: "SUPPORTED", 1: "NOT_SUPPORTED"}
    return mapping.get(int(label), str(label))


def _convert(example: Dict[str, Any], split: str, idx: int) -> Dict[str, Any]:
    supporting_facts = [
        {"key": str(fact["key"]), "value": int(fact["value"])}
        for fact in example["supporting_facts"]
    ]
    return {
        "case_id": f"hover-{split}-{idx}",
        "task_type": "claim_verification_retrieval",
        "context": {"claim": str(example["claim"])},
        "expected": {
            "supporting_facts": supporting_facts,
            "label": _label_name(example["label"]),
            "label_raw": int(example["label"]) if not isinstance(example["label"], str) else example["label"],
        },
        "metadata": {
            "source": "hover",
            "split": split,
            "original_id": example.get("id"),
            "original_uid": example.get("uid"),
            "num_hops": example.get("num_hops"),
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

    raw = list(load_dataset("hover")["train"])
    filtered = [
        {
            "claim": ex["claim"],
            "supporting_facts": ex["supporting_facts"],
            "label": ex["label"],
            "id": ex.get("id"),
            "uid": ex.get("uid"),
            "num_hops": ex.get("num_hops"),
        }
        for ex in raw
        if _count_unique_docs(ex) == 3
    ]

    rng = random.Random()
    rng.seed(0)
    rng.shuffle(filtered)

    total_len = len(filtered)
    # Mirror ``Benchmark.create_splits``: first 40% → test, next 40% → val, last 20% → train.
    test_pool = filtered[: int(0.4 * total_len)]
    val_pool = filtered[int(0.4 * total_len) : int(0.8 * total_len)]
    train_pool = filtered[int(0.8 * total_len) :]

    train = _trim(train_pool, TRAIN_CAP)
    val = _trim(val_pool, VAL_CAP)
    test = _trim(test_pool, TEST_CAP)

    train_cases = [_convert(ex, "train", i) for i, ex in enumerate(train)]
    val_cases = [_convert(ex, "val", i) for i, ex in enumerate(val)]
    test_cases = [_convert(ex, "test", i) for i, ex in enumerate(test)]

    _write_split(output_dir / "train.jsonl", train_cases)
    _write_split(output_dir / "val.jsonl", val_cases)
    _write_split(output_dir / "test.jsonl", test_cases)

    gepa_path = Path(__file__).resolve().parents[4] / "gepa-artifact"
    meta = {
        "benchmark": "hoverBench",
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
    parser = argparse.ArgumentParser(description="Build HoVer dataset splits mirroring GEPA's hoverBench.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    counts = build(args.output_dir)
    for name, n in counts.items():
        print(f"  {name}.jsonl: {n} cases")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
