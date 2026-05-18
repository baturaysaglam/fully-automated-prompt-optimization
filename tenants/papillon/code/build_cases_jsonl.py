# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build Papillon (PUPA) evaluation datasets from HuggingFace.

Produces three JSONL files with fixed sequential splits:
  - train.jsonl — 111 cases
  - val.jsonl   — 111 cases
  - test.jsonl  — 221 cases

Usage:
    python tenants/papillon/code/build_cases_jsonl.py
"""

from __future__ import annotations

import json
from pathlib import Path

from datasets import load_dataset

OUTPUT_DIR = Path("tenants/papillon/datasets/datasets")


def _convert_case(row: dict, idx: int) -> dict:
    """Convert a HuggingFace PUPA row to FAPO eval case format."""
    return {
        "case_id": f"papillon_{idx:04d}",
        "task_type": "privacy_preserving",
        "context": {
            "query": row["user_query"],
            "pii_str": row.get("pii_units", ""),
        },
        "expected": {
            "target_response": row.get("target_response", ""),
            "pii_str": row.get("pii_units", ""),
        },
        "metadata": {
            "source": "Columbia-NLP/PUPA",
            "category": row.get("predicted_category", ""),
        },
    }


def build_all() -> dict[str, int]:
    """Load PUPA from HuggingFace and split sequentially."""
    ds = load_dataset("Columbia-NLP/PUPA", "pupa_new", split="train")
    dataset = [row for row in ds]

    # Fixed sequential split (664 total → 111/111/442)
    train_data = dataset[:111]
    val_data = dataset[111:222]
    test_data = dataset[222:]

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
                f.write(json.dumps(c) + "\n")
        counts[split_name] = len(cases)
        print(f"Wrote {len(cases)} {split_name} cases to {out}")

    return counts


if __name__ == "__main__":
    counts = build_all()
    print(f"\nDone. train={counts['train']}, val={counts['val']}, test={counts['test']}")
