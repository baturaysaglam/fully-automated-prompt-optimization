# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build LiveBench Math evaluation datasets from HuggingFace.

Produces three JSONL files:
  - train.jsonl — 121 problems (for optimization)
  - val.jsonl   — 121 problems (for validation)
  - test.jsonl  — 126 problems (for final evaluation)

Splits follow GEPA: HuggingFace 'livebench/math' test split, shuffled with
seed=0, divided at 33%/66% boundaries.

Usage:
    python tenants/livebench_math/code/build_cases_jsonl.py
"""

from __future__ import annotations

import json
import random
from datetime import date, datetime
from pathlib import Path

from datasets import load_dataset


class _DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

OUTPUT_DIR = Path("tenants/livebench_math/datasets/datasets")


def _convert_case(row: dict, idx: int) -> dict:
    """Convert a HuggingFace LiveBench Math row to FAPO eval case format."""
    question_text = row["turns"][0]
    question_id = row.get("question_id", f"livebench_math_{idx:04d}")

    return {
        "case_id": question_id,
        "task_type": "math",
        "context": {"question": question_text},
        "expected": {
            "question_d": row,
        },
        "metadata": {
            "source": "livebench/math",
            "task": row.get("task", ""),
            "subtask": row.get("subtask", ""),
            "category": row.get("category", ""),
        },
    }


def build_all() -> dict[str, int]:
    """Load LiveBench Math from HuggingFace and split into train/val/test."""
    ds = load_dataset("livebench/math", split="test")
    dataset = [row for row in ds]

    random.Random(0).shuffle(dataset)
    tot = len(dataset)

    split_1 = int(tot * 0.33)
    split_2 = int(tot * 0.66)

    train_data = dataset[:split_1]
    val_data = dataset[split_1:split_2]
    test_data = dataset[split_2:]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    counts = {}
    for split_name, split_data in [
        ("train", train_data),
        ("val", val_data),
        ("test", test_data),
    ]:
        cases = [_convert_case(row, i) for i, row in enumerate(split_data)]
        out = OUTPUT_DIR / f"{split_name}.jsonl"
        with open(out, "w") as f:
            for c in cases:
                f.write(json.dumps(c, cls=_DateEncoder) + "\n")
        counts[split_name] = len(cases)
        print(f"Wrote {len(cases)} {split_name} cases to {out}")

    return counts


if __name__ == "__main__":
    counts = build_all()
    print(f"\nDone. train={counts['train']}, val={counts['val']}, test={counts['test']}")
