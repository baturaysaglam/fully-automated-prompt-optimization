#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Assemble an experiment manifest from optimize-loop round files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.hephaestus.experiment.manifest import build_manifest, write_manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble experiment manifest from optimization loop output.",
    )
    parser.add_argument("--tenant", required=True, help="Tenant ID")
    parser.add_argument("--log-dir", required=True, help="Path to the optimize-loop log directory")
    parser.add_argument("--task-model", default="gpt-4.1-mini", help="Task model used for evaluation")
    parser.add_argument("--started-at", required=True, help="Experiment start time (ISO 8601)")
    parser.add_argument("--completed-at", required=True, help="Experiment end time (ISO 8601)")
    parser.add_argument("--duration", required=True, type=float, help="Total duration in seconds")
    parser.add_argument("--status", required=True, choices=["success", "max_rounds", "error"])
    parser.add_argument("--rounds", required=True, type=int, help="Total rounds executed")

    args = parser.parse_args()
    log_dir = Path(args.log_dir)

    if not log_dir.is_dir():
        print(f"Log directory not found: {log_dir}", file=sys.stderr)
        raise SystemExit(1)

    manifest = build_manifest(
        log_dir=log_dir,
        tenant_id=args.tenant,
        task_model=args.task_model,
        started_at=args.started_at,
        completed_at=args.completed_at,
        duration_seconds=args.duration,
        status=args.status,
        total_rounds=args.rounds,
    )

    output_path = log_dir / "experiment-manifest.json"
    write_manifest(manifest, output_path)
    print(f"Manifest written to: {output_path}")

    summary = manifest.agent_summary
    print(f"  Total agent calls: {summary['total_agent_calls']}")
    for agent, count in sorted(summary.get("by_agent", {}).items()):
        print(f"    {agent}: {count}")
    for model, count in sorted(summary.get("by_model", {}).items()):
        print(f"    [{model}]: {count}")


if __name__ == "__main__":
    main()
