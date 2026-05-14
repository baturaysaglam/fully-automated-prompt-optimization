#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build Hephaestus JSONL dataset from CTIBench RCM via faith's data loader.

Uses faith's ``load_data()`` to get a fully-transformed DataFrame (with
row-391 fix, whitespace cleaning, and label uppercasing already applied),
then converts each row to Hephaestus case format.

Supports ``--split`` to produce stratified dev/test splits from an existing
``test.jsonl`` (or ``all.jsonl``).
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("tenants/cti_rcm/datasets/datasets")


def _build_cases(output_dir: Path) -> int:
    from faith._internal.io.benchmarks import benchmarks_root
    from faith.benchmark.config import load_config_from_path
    from faith.benchmark.dataset.load import load_data

    benchmark_path = benchmarks_root() / "ctibench-rcm"
    config = load_config_from_path(benchmark_path)
    df, _ = load_data("ctibench-rcm", benchmark_path, config["source"])

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "test.jsonl"

    with out_path.open("w", encoding="utf-8") as f:
        for idx, row in df.iterrows():
            case = {
                "case_id": str(idx),
                "task_type": "root_cause_mapping",
                "context": {"description": row["question"]},
                "expected": {"cwe_id": row["answer"]},
                "metadata": {"source": "AI4Sec/cti-bench", "subset": "cti-rcm"},
            }
            f.write(json.dumps(case))
            f.write("\n")

    return len(df)


def _write_jsonl(cases: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case))
            f.write("\n")


def _split_dataset(
    output_dir: Path,
    dev_fraction: float,
    seed: int,
    rare_threshold: int,
) -> tuple[int, int]:
    from src.hephaestus.datasets.stratified_split import stratified_split_by_key

    output_dir.mkdir(parents=True, exist_ok=True)

    # Read from all.jsonl if it exists, otherwise from test.jsonl
    all_path = output_dir / "all.jsonl"
    test_path = output_dir / "test.jsonl"

    if all_path.exists():
        source = all_path
    elif test_path.exists():
        source = test_path
    else:
        raise FileNotFoundError(
            f"No dataset found at {all_path} or {test_path}. "
            "Run without --split first to build from faith."
        )

    cases = []
    with source.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    # Preserve the full dataset as all.jsonl before splitting
    if not all_path.exists():
        shutil.copy2(source, all_path)

    dev, test = stratified_split_by_key(
        cases,
        key_fn=lambda c: c["expected"]["cwe_id"],
        dev_fraction=dev_fraction,
        seed=seed,
        rare_threshold=rare_threshold,
    )

    _write_jsonl(dev, output_dir / "dev.jsonl")
    _write_jsonl(test, output_dir / "test.jsonl")

    return len(dev), len(test)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Hephaestus JSONL from CTIBench RCM via faith.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write dataset files",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Split existing test.jsonl into dev.jsonl + test.jsonl",
    )
    parser.add_argument("--dev-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rare-threshold", type=int, default=3)
    args = parser.parse_args()

    if args.split:
        print("Splitting dataset into dev/test...")
        n_dev, n_test = _split_dataset(
            args.output_dir, args.dev_fraction, args.seed, args.rare_threshold,
        )
        print(f"  dev.jsonl:  {n_dev} cases")
        print(f"  test.jsonl: {n_test} cases")
        print(f"  all.jsonl:  {n_dev + n_test} cases (full dataset preserved)")
    else:
        print("Loading CTIBench RCM via faith...")
        count = _build_cases(args.output_dir)
        print(f"  test.jsonl: {count} cases")

    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
