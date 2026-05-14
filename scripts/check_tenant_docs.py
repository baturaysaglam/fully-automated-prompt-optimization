#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED_FILES = [
    "README.md",
    "docs/tenant-profile.md",
    "docs/data-contract.md",
    "docs/prompt-contract.md",
    "docs/eval-operations.md",
    "docs/iteration-playbook.md",
    "docs/change-log.md",
    "docs/docs-index.yaml",
]

REQUIRED_DOC_SECTIONS: Dict[str, List[str]] = {
    "docs/tenant-profile.md": [
        "## Organization Profile",
        "## Security Environment Assumptions",
        "## Threat Model Focus",
        "## Known Safe Patterns",
        "## Tenant Terminology",
    ],
    "docs/data-contract.md": [
        "## Dataset Inventory",
        "## Case Schema",
        "## Label Taxonomy",
        "## Check Expectations",
        "## Dataset Update Procedure",
    ],
    "docs/prompt-contract.md": [
        "## Output Format Contract",
        "## Decision Policy",
        "## Defang and Safety Rules",
        "## Variant Strategy",
        "## Non-Goals",
    ],
    "docs/eval-operations.md": [
        "## Config Matrix",
        "## Standard Eval Commands",
        "## Success Criteria",
        "## Failure Triage",
        "## Output Management",
    ],
    "docs/iteration-playbook.md": [
        "## Prerequisites",
        "## Iteration Loop",
        "## Stop Criteria",
        "## Regression Prevention",
        "## Lessons Logging",
    ],
}

REQUIRED_INDEX_KEYS = ["version", "tenant_id", "canonical_docs", "last_validated"]
REQUIRED_CANONICAL_DOC_KEYS = [
    "tenant_profile",
    "data_contract",
    "prompt_contract",
    "eval_operations",
    "iteration_playbook",
    "change_log",
]


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_docs_index(path: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    top: Dict[str, str] = {}
    canonical_docs: Dict[str, str] = {}
    canonical_indent = -1

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip("\n")
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:\s*.*$", line):
            key, _, value = line.partition(":")
            key = key.strip()
            value = _strip_quotes(value)
            top[key] = value
            canonical_indent = indent if key == "canonical_docs" else -1
            continue

        if canonical_indent >= 0:
            if indent <= canonical_indent:
                canonical_indent = -1
                continue
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:\s*.*$", stripped):
                key_part, _, value_part = stripped.partition(":")
                canonical_docs[key_part] = _strip_quotes(value_part)

    return top, canonical_docs


def check_tenant(tenant_dir: Path) -> List[str]:
    errors: List[str] = []
    tenant_root_resolved = tenant_dir.resolve()

    for rel_path in REQUIRED_FILES:
        full_path = tenant_dir / rel_path
        if not full_path.exists():
            errors.append(f"{tenant_dir.name}: missing required file `{rel_path}`")

    for rel_path, required_sections in REQUIRED_DOC_SECTIONS.items():
        full_path = tenant_dir / rel_path
        if not full_path.exists():
            continue
        text = full_path.read_text(encoding="utf-8")
        for section in required_sections:
            if section not in text:
                errors.append(f"{tenant_dir.name}: `{rel_path}` missing section `{section}`")

    index_path = tenant_dir / "docs/docs-index.yaml"
    if index_path.exists():
        top, canonical_docs = parse_docs_index(index_path)
        for key in REQUIRED_INDEX_KEYS:
            if key not in top:
                errors.append(f"{tenant_dir.name}: docs-index missing key `{key}`")
        for key in REQUIRED_CANONICAL_DOC_KEYS:
            if key not in canonical_docs:
                errors.append(f"{tenant_dir.name}: docs-index missing canonical doc key `{key}`")
                continue
            mapped_raw = tenant_dir / canonical_docs[key]
            mapped = mapped_raw.resolve()
            try:
                mapped.relative_to(tenant_root_resolved)
            except ValueError:
                errors.append(
                    f"{tenant_dir.name}: docs-index maps `{key}` outside tenant root: `{canonical_docs[key]}`"
                )
                continue
            if not mapped.exists():
                errors.append(
                    f"{tenant_dir.name}: docs-index maps `{key}` to missing path `{canonical_docs[key]}`"
                )

        tenant_id = top.get("tenant_id", "")
        if tenant_id and tenant_id != tenant_dir.name:
            errors.append(
                f"{tenant_dir.name}: docs-index tenant_id `{tenant_id}` does not match directory name"
            )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate tenant documentation contract.")
    parser.add_argument(
        "--tenant-root",
        default="tenants",
        help="Root folder containing tenant directories (default: tenants).",
    )
    parser.add_argument(
        "--tenant",
        default=None,
        help="Optional tenant directory name to validate only one tenant.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tenant_root = Path(args.tenant_root)
    if not tenant_root.exists():
        print(f"Tenant root not found: {tenant_root}", file=sys.stderr)
        return 2

    if args.tenant:
        tenant_dirs = [tenant_root / args.tenant]
    else:
        tenant_dirs = sorted([
            p for p in tenant_root.iterdir()
            if p.is_dir() and p.name != "__pycache__"
        ])

    all_errors: List[str] = []
    for tenant_dir in tenant_dirs:
        if not tenant_dir.exists():
            all_errors.append(f"tenant not found: {tenant_dir.name}")
            continue
        all_errors.extend(check_tenant(tenant_dir))

    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print(f"Tenant docs contract check passed for {len(tenant_dirs)} tenant(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
