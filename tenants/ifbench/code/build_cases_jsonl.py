# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build IFBench evaluation datasets from source artifacts.

Produces three JSONL files:
  - val.jsonl   — 300 cases (rows 0-299 of IFBench_train.jsonl)
  - train.jsonl — 150 cases (rows 300-449 of IFBench_train.jsonl)
  - test.jsonl  — 294 cases (all of IFBench_test.jsonl)

Splits follow GEPA exactly.

Usage:
    python tenants/ifbench/code/build_cases_jsonl.py
"""

from __future__ import annotations

import json
from pathlib import Path

SOURCE_DIR = Path("tenants/ifbench/source_artifacts")
OUTPUT_DIR = Path("tenants/ifbench/datasets/datasets")


def _convert_case(row: dict, idx: int, source: str) -> dict:
    """Convert a raw IFBench row to FAPO eval case format."""
    return {
        "case_id": f"ifbench_{source}_{idx:04d}",
        "task_type": "instruction_following",
        "context": {"prompt": row["prompt"]},
        "expected": {
            "instruction_id_list": row["instruction_id_list"],
            "kwargs": row["kwargs"],
        },
        "metadata": {
            "source": f"IFBench_{source}",
        },
    }


def build_all() -> dict[str, int]:
    """Read source artifacts and produce train/val/test splits."""
    # Read train source (14971 lines)
    train_rows = []
    with open(SOURCE_DIR / "IFBench_train.jsonl") as f:
        for line in f:
            train_rows.append(json.loads(line))

    # Read test source (294 lines)
    test_rows = []
    with open(SOURCE_DIR / "IFBench_test.jsonl") as f:
        for line in f:
            test_rows.append(json.loads(line))

    # Split per GEPA: val=0:300, train=300:450
    val_data = train_rows[:300]
    train_data = train_rows[300:450]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    counts = {}
    for split_name, split_data, source_label in [
        ("val", val_data, "train"),
        ("train", train_data, "train"),
        ("test", test_rows, "test"),
    ]:
        cases = [_convert_case(row, i, source_label) for i, row in enumerate(split_data)]
        out = OUTPUT_DIR / f"{split_name}.jsonl"
        with open(out, "w") as f:
            for c in cases:
                f.write(json.dumps(c) + "\n")
        counts[split_name] = len(cases)
        print(f"Wrote {len(cases)} {split_name} cases to {out}")

    return counts


if __name__ == "__main__":
    counts = build_all()
    print(f"\nDone. train={counts['train']}, val={counts['val']}, test={counts['test']}")
