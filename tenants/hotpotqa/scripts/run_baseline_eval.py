#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Run the full HotpotQA baseline evaluation pipeline.

This script handles the complete eval workflow:
  1. Builds train/val/test JSONL splits from HuggingFace fullwiki (if not present)
  2. Runs the full chain eval (BM25 retrieval is in-process, no server needed)
  3. Prints summary

Prerequisites:
  - OPENAI_API_KEY must be set in the environment
  - Run via: python tenants/hotpotqa/scripts/run_baseline_eval.py
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TENANT_ROOT = PROJECT_ROOT / "tenants" / "hotpotqa"
DATASET_DIR = TENANT_ROOT / "datasets" / "datasets"


def _check_api_key() -> None:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        print("ERROR: OPENAI_API_KEY not set in environment.")
        print("Run with: python tenants/hotpotqa/scripts/run_baseline_eval.py")
        sys.exit(1)
    print("  OPENAI_API_KEY: set")


def _ensure_dataset(split: str) -> Path:
    dataset_path = DATASET_DIR / f"{split}.jsonl"
    if dataset_path.exists():
        count = sum(1 for _ in dataset_path.open())
        print(f"  Dataset: {dataset_path} ({count} cases)")
        return dataset_path

    print("  Building dataset splits from HuggingFace fullwiki...")
    sys.path.insert(0, str(PROJECT_ROOT))
    from tenants.hotpotqa.code.build_cases_jsonl import (
        _load_fullwiki_pools,
        build_splits,
    )

    train_pool, dev_pool, test_pool = _load_fullwiki_pools()
    counts = build_splits(train_pool, dev_pool, test_pool, DATASET_DIR)
    for name, n in counts.items():
        print(f"    {name}.jsonl: {n} cases")

    return dataset_path


def _run_eval(config: dict, config_path: str, split: str) -> None:
    config = json.loads(json.dumps(config))
    config["dataset"]["path"] = str(DATASET_DIR / f"{split}.jsonl")

    # Write patched config to a temp file next to the original.
    patched_path = Path(config_path).with_suffix(".tmp.json")
    with open(patched_path, "w") as f:
        json.dump(config, f, indent=2)

    split_path = DATASET_DIR / f"{split}.jsonl"
    case_count = sum(1 for _ in split_path.open())
    print(f"\n  Running eval with config: {config_path}")
    print(f"  Split: {split} ({case_count} cases)")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "hephaestus.cli", "eval", "--config", str(patched_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"ERROR: Eval failed (exit code {result.returncode})")
            print(f"stdout: {result.stdout[-500:]}")
            print(f"stderr: {result.stderr[-500:]}")
            sys.exit(1)
        print("  Eval completed successfully")
    finally:
        patched_path.unlink(missing_ok=True)


def _print_summary(output_dir: Path) -> None:
    summary_path = output_dir / "summary.md"
    results_path = output_dir / "results.jsonl"

    if summary_path.exists():
        print("\n=== SUMMARY ===")
        print(summary_path.read_text())

    if results_path.exists():
        results = [json.loads(line) for line in results_path.open()]
        step_keys = set()
        for r in results:
            step_keys.update(r.get("step_outputs", {}).keys())
        print(f"\nTotal cases: {len(results)}")
        print(f"Unique step_output keys: {sorted(step_keys)} ({len(step_keys)} keys)")

        # EM breakdown
        em_scores = [r.get("score_breakdown", {}).get("exact_match", 0) for r in results]
        if em_scores:
            em_pct = sum(1 for s in em_scores if s == 100.0) / len(em_scores) * 100
            print(f"Exact Match accuracy: {em_pct:.1f}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HotpotQA baseline evaluation")
    parser.add_argument(
        "--split",
        choices=["train", "val", "test"],
        default="val",
        help="Dataset split to evaluate (default: val)",
    )
    args = parser.parse_args()

    print("=== HotpotQA Baseline Evaluation ===\n")

    print("[1/3] Checking prerequisites...")
    _check_api_key()

    print("\n[2/3] Ensuring dataset...")
    _ensure_dataset(args.split)

    CONFIG_MAP = {
        "train": "local-chain-variant001-train.json",
        "test": "local-chain-variant001-test.json",
        "val": "local-chain-variant001.json",
    }
    config_name = CONFIG_MAP[args.split]
    config_path = str(TENANT_ROOT / "configs" / config_name)
    with open(config_path) as f:
        config = json.load(f)
    output_dir = Path(config["output_dir"])

    print("\n[3/3] Running evaluation...")
    _run_eval(config, config_path, args.split)

    print("\n=== Results ===")
    _print_summary(PROJECT_ROOT / output_dir)


if __name__ == "__main__":
    main()
