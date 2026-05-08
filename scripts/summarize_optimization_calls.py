#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Summarize a single optimization run's sub-agent call log.

Reads ``tenants/<tenant>/evals/<run>/optimization-calls.jsonl`` and emits a
single JSON object suitable for appending to
``tenants/<tenant>/docs/iteration-memory.jsonl``.

Example:
    python scripts/summarize_optimization_calls.py --run abc123 --tenant hotpotqa
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Make src.hephaestus importable when running from the repo root.
sys.path.insert(0, str(REPO_ROOT))

from src.hephaestus.optimization.call_tracker import summarize  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize an optimization-run sub-agent call log.")
    parser.add_argument(
        "--run",
        required=True,
        help="Optimization run id (file stem under tenants/<tenant>/evals/).",
    )
    parser.add_argument("--tenant", required=True, help="Tenant id, e.g. hotpotqa.")
    parser.add_argument(
        "--output",
        default="-",
        help="Output path. '-' writes to stdout (default).",
    )
    args = parser.parse_args()

    log_path = REPO_ROOT / "tenants" / args.tenant / "evals" / args.run / "optimization-calls.jsonl"
    summary = summarize(log_path)
    block = {
        "iteration_id": args.run,
        "tenant_id": args.tenant,
        "bigger_model_calls": summary.to_dict(),
    }
    payload = json.dumps(block, sort_keys=True)
    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
