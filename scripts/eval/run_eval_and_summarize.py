#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Run a tenant eval config and print summary + output directory."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def _print_and_exit(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    raise SystemExit(result.returncode)


def _load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_eval(config_path: Path) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "hephaestus.cli", "eval", "--config", str(config_path)]
    return _run_command(cmd)


def _run_with_optional_output_override(
    args: argparse.Namespace,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    config_path = Path(args.config)
    config = _load_config(config_path)
    output_dir = Path(config["output_dir"])

    if not args.output_dir:
        return _run_eval(config_path), output_dir

    output_dir = Path(args.output_dir)
    config["output_dir"] = str(output_dir)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(config, tmp)
        tmp_path = Path(tmp.name)
    try:
        return _run_eval(tmp_path), output_dir
    finally:
        tmp_path.unlink(missing_ok=True)


def run_eval_and_print(args: argparse.Namespace) -> None:
    result, output_dir = _run_with_optional_output_override(args)
    if result.returncode != 0:
        _print_and_exit(result)

    summary_path = output_dir / "summary.md"
    if not summary_path.exists():
        print(f"Summary not found: {summary_path}", file=sys.stderr)
        raise SystemExit(3)

    run_config_path = output_dir / "run_config.json"
    if run_config_path.exists():
        rc = json.loads(run_config_path.read_text(encoding="utf-8"))
        run_id = rc.get("run_id", "")
        if run_id:
            print(f"Run ID: {run_id}")

    summary_text = summary_path.read_text(encoding="utf-8").rstrip()
    print(f"Evaluation output directory: {output_dir}")
    print()
    print(summary_text)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tenant eval config and print summary + output directory.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to eval config JSON (e.g., tenants/<tenant_id>/configs/local-<run-name>.json).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory override without editing the local config file.",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    run_eval_and_print(args)


if __name__ == "__main__":
    main()
