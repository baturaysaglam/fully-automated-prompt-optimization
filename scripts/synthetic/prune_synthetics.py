#!/usr/bin/env python
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Prune noncompliant synthetic examples and normalize placeholder hashes.

Default mode is dry-run; use --apply to make changes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
from pathlib import Path

GREET_RE = re.compile(r"\b(hi|hello|dear|greetings)\b", re.IGNORECASE)
SIGN_RE = re.compile(r"\b(regards|sincerely|thanks|thank you|best|respectfully)\b", re.IGNORECASE)
PLACEHOLDER_HASH_RE = re.compile(r"^(.)\1{31,}$")


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def has_greeting_or_signature(text: str) -> tuple[bool, bool]:
    return bool(GREET_RE.search(text)), bool(SIGN_RE.search(text))


def deterministic_hash(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def load_email_body(example_dir: Path) -> tuple[Path | None, str]:
    body_path = example_dir / "Context - Email Body.pdf.txt"
    if body_path.exists():
        return body_path, body_path.read_text(encoding="utf-8")
    return None, ""


def find_examples(examples_dir: Path) -> list[Path]:
    return sorted([p for p in examples_dir.iterdir() if p.is_dir()])


def remove_examples(example_dirs: list[Path], apply: bool) -> None:
    for d in example_dirs:
        if apply:
            shutil.rmtree(d)
        print(f"REMOVE: {d}")


def _pick_id_field(fieldnames: list[str]) -> str | None:
    for candidate in ("example", "example_id"):
        if candidate in fieldnames:
            return candidate
    return fieldnames[0] if fieldnames else None


def update_csv(csv_path: Path, removed_names: set[str], apply: bool) -> None:
    if not csv_path.exists():
        return
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        id_field = _pick_id_field(fieldnames)
        rows = []
        for row in reader:
            if id_field and row.get(id_field) in removed_names:
                continue
            rows.append({name: row.get(name, "") for name in fieldnames})
    if apply:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    print(f"UPDATE CSV: {csv_path}")


def normalize_hashes(example_dirs: list[Path], apply: bool) -> None:
    for d in example_dirs:
        sw_path = d / "Context - Stealth Watch.pdf.txt"
        if not sw_path.exists():
            continue
        text = sw_path.read_text(encoding="utf-8")
        lines = []
        changed = False
        for line in text.splitlines():
            if line.strip().startswith("attachments_sha256:"):
                value = line.split(":", 1)[1].strip().strip('"')
                if PLACEHOLDER_HASH_RE.match(value):
                    new_value = deterministic_hash(f"{d.name}::synthetic")
                    line = f'attachments_sha256: "{new_value}"'
                    changed = True
            lines.append(line)
        if changed:
            if apply:
                sw_path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
            print(f"FIX HASH: {sw_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples-dir", default="reports/synthetic_artifacts")
    parser.add_argument("--max-words", type=int, default=10)
    parser.add_argument("--apply", action="store_true", help="Apply changes; otherwise dry-run")
    args = parser.parse_args()

    examples_dir = Path(args.examples_dir)
    if not examples_dir.exists():
        raise SystemExit(f"Missing examples dir: {examples_dir}")

    severe = []
    for d in find_examples(examples_dir):
        body_path, body_text = load_email_body(d)
        if not body_path:
            continue
        wc = word_count(body_text)
        has_greet, has_sign = has_greeting_or_signature(body_text)
        if wc <= args.max_words and not (has_greet or has_sign):
            severe.append(d)

    removed_names = {d.name for d in severe}

    if severe:
        remove_examples(severe, apply=args.apply)
        update_csv(examples_dir / "labels_review.csv", removed_names, apply=args.apply)
        update_csv(examples_dir / "hard_labels_review.csv", removed_names, apply=args.apply)
    else:
        print("No severe-violation examples found.")

    normalize_hashes(find_examples(examples_dir), apply=args.apply)

    if not args.apply:
        print("Dry-run only. Re-run with --apply to make changes.")


if __name__ == "__main__":
    main()
