#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build Hephaestus JSONL splits mirroring GEPA's ``Papillon``.

Replicates :class:`gepa_artifact.benchmarks.papillon.papillon_data.Papillon`:

1. Load HuggingFace ``Columbia-NLP/PUPA`` config ``pupa_new`` train (664 rows).
2. Hardcoded sequential slices:
   - train = [:111]
   - val   = [111:222]
   - test  = [222:443]
3. ``trim_dataset(seed=1)`` is a no-op (each subset is below the cap).

This builder imports only ``papillon_data`` — not the package ``__init__.py``
— because the package's ``__init__.py`` instantiates
``dspy.LM(model="openai/gpt-4.1-mini")`` at import time and would require
``OPENAI_API_KEY`` even for data-only use. We avoid that trap by loading the
HF data directly and applying the same slicing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_OUTPUT_DIR = Path("tenants/papillon/datasets/datasets")

NUM_TRAIN = 111
NUM_VAL = 111
NUM_TEST = 221


def _parse_pii_units(pii_str: str) -> List[str]:
    """Mirror ``LLMJudge.forward``'s split-and-dedupe of ``pii_str``."""
    if not pii_str:
        return []
    units = [u.strip() for u in pii_str.split("||")]
    # Preserve order but de-dupe (GEPA uses ``list(set(...))`` which is order-
    # sensitive in Python; we prefer stable ordering for byte-level determinism).
    seen = set()
    result: List[str] = []
    for u in units:
        if u and u not in seen:
            seen.add(u)
            result.append(u)
    return result


def _convert(example: Dict[str, Any], split: str, idx: int) -> Dict[str, Any]:
    pii_str = str(example.get("pii_units", ""))
    return {
        "case_id": f"papillon-{split}-{idx}",
        "task_type": "privacy_utility",
        "context": {"user_query": str(example["user_query"])},
        "expected": {
            "target_response": str(example["target_response"]),
            "pii_str": pii_str,
            "pii_units": _parse_pii_units(pii_str),
        },
        "metadata": {
            "source": "Columbia-NLP/PUPA/pupa_new",
            "split": split,
            "conversation_hash": example.get("conversation_hash"),
            "predicted_category": example.get("predicted_category"),
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

    raw = list(load_dataset("Columbia-NLP/PUPA", "pupa_new")["train"])
    train = raw[:NUM_TRAIN]
    val = raw[NUM_TRAIN : NUM_TRAIN + NUM_VAL]
    test = raw[NUM_TRAIN + NUM_VAL : NUM_TRAIN + NUM_VAL + NUM_TEST]
    assert len(train) == NUM_TRAIN
    assert len(val) == NUM_VAL
    assert len(test) == NUM_TEST

    train_cases = [_convert(ex, "train", i) for i, ex in enumerate(train)]
    val_cases = [_convert(ex, "val", i) for i, ex in enumerate(val)]
    test_cases = [_convert(ex, "test", i) for i, ex in enumerate(test)]

    _write_split(output_dir / "train.jsonl", train_cases)
    _write_split(output_dir / "val.jsonl", val_cases)
    _write_split(output_dir / "test.jsonl", test_cases)

    gepa_path = Path(__file__).resolve().parents[4] / "gepa-artifact"
    meta = {
        "benchmark": "Papillon",
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
    parser = argparse.ArgumentParser(description="Build Papillon dataset splits mirroring GEPA's Papillon.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    counts = build(args.output_dir)
    for name, n in counts.items():
        print(f"  {name}.jsonl: {n} cases")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
