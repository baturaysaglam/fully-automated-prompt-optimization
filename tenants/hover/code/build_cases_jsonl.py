# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build HoVer evaluation datasets from HuggingFace.

Produces three JSONL files:
  - train.jsonl — 150 cases (3-hop claims for optimization)
  - val.jsonl   — 300 cases (3-hop claims for validation)
  - test.jsonl  — 300 cases (3-hop claims for final evaluation)

Filters to 3-hop examples only, matching GEPA's setup.

Usage:
    python tenants/hover/code/build_cases_jsonl.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from datasets import load_dataset

OUTPUT_DIR = Path("tenants/hover/datasets/datasets")


def _convert_case(row: dict, idx: int) -> dict:
    """Convert a HuggingFace HoVer row to FEPO eval case format."""
    return {
        "case_id": f"hover_{row.get('uid', idx)}",
        "task_type": "claim_verification",
        "context": {"claim": row["claim"]},
        "expected": {
            "supporting_titles": row["supporting_facts"],
            "label": row.get("label", ""),
        },
        "metadata": {
            "source": "hover",
            "num_hops": row.get("num_hops", 3),
        },
    }


def build_all() -> dict[str, int]:
    """Load HoVer from HuggingFace, filter 3-hop, and split."""
    ds = load_dataset("hover-nlp/hover", "corpus", split="train")

    # Filter to 3-hop examples
    three_hop = [row for row in ds if row.get("num_hops", 0) == 3]

    random.Random(42).shuffle(three_hop)

    train_data = three_hop[:150]
    val_data = three_hop[150:450]
    test_data = three_hop[450:750]

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
