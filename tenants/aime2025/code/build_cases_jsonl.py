# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build AIME evaluation datasets from HuggingFace.

Produces two JSONL files:
  - train.jsonl — 90 problems from AIME 2022-2024 (for optimization)
  - test.jsonl  — 30 problems from AIME 2025 (for final evaluation)

Matches the exact splits from ETGPO (arxiv 2602.00997).

Usage:
    python tenants/aime2025/code/build_cases_jsonl.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from datasets import load_dataset

OUTPUT_DIR = Path("tenants/aime2025/datasets/datasets")


def build_train() -> int:
    """Build train set from AIME 2022-2024 (AI-MO/aimo-validation-aime)."""
    ds = load_dataset("AI-MO/aimo-validation-aime", split="train")
    cases = []
    for row in ds:
        url = row.get("url", "")
        m = re.search(r"(\d{4})_AIME_(I+)_Problems/Problem_(\d+)", url)
        if not m:
            continue
        year = int(m.group(1))
        exam = m.group(2)
        pnum = int(m.group(3))
        case = {
            "case_id": f"aime_{year}_{exam}_{pnum:02d}",
            "task_type": "math_competition",
            "context": {"problem": row["problem"]},
            "expected": {"answer": str(row["answer"]).strip()},
            "metadata": {
                "source": "AI-MO/aimo-validation-aime",
                "year": year,
                "exam": exam,
                "problem_number": pnum,
                "url": url,
            },
        }
        cases.append(case)

    cases.sort(key=lambda c: c["case_id"])
    out = OUTPUT_DIR / "train.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
    print(f"Wrote {len(cases)} train cases to {out}")
    return len(cases)


def build_test() -> int:
    """Build test set from AIME 2025."""
    ds = load_dataset("yentinglin/aime_2025", "default", split="train")
    cases = []
    for row in ds:
        url = row.get("url", "")
        if "AIME_II" in url:
            exam = "II"
        else:
            exam = "I"
        pnum = int(row["id"]) + 1  # 0-indexed -> 1-indexed
        # Reset numbering for part II (ids 15-29 -> 1-15)
        if pnum > 15:
            pnum -= 15
        case = {
            "case_id": f"aime_2025_{exam}_{pnum:02d}",
            "task_type": "math_competition",
            "context": {"problem": row["problem"]},
            "expected": {"answer": str(row["answer"]).strip()},
            "metadata": {
                "source": "yentinglin/aime_2025",
                "year": 2025,
                "exam": exam,
                "problem_number": pnum,
                "url": url,
            },
        }
        cases.append(case)

    cases.sort(key=lambda c: c["case_id"])
    out = OUTPUT_DIR / "test.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
    print(f"Wrote {len(cases)} test cases to {out}")
    return len(cases)


if __name__ == "__main__":
    n_train = build_train()
    n_test = build_test()
    print(f"\nDone. train={n_train}, test={n_test}")
