#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build collection.tsv from HotpotQA Wikipedia abstracts tarball.

The raw abstracts tarball contains bz2-compressed JSON files. Each JSON
document has: id, url, title, text (list of paragraph strings).

Output: /data/collection.tsv with format ``pid\\tpassage_text`` (0-indexed).
"""
from __future__ import annotations

import bz2
import json
import os
import sys
import tarfile

ABSTRACTS_TAR = os.environ.get("ABSTRACTS_TAR", "/data/abstracts.tar.bz2")
OUTPUT_TSV = os.environ.get("OUTPUT_TSV", "/data/collection.tsv")
MIN_PARAGRAPH_LEN = 50


def extract_passages(tar_path: str) -> list[str]:
    """Parse bz2 JSON files from the tarball and extract passages."""
    passages: list[str] = []
    count = 0

    with tarfile.open(tar_path, "r:bz2") as tar:
        for member in tar:
            if not member.isfile():
                continue
            f = tar.extractfile(member)
            if f is None:
                continue

            # Each file inside the tar is itself bz2-compressed JSON lines
            raw = f.read()
            # Try reading as bz2 first; fall back to plain text
            try:
                data = bz2.decompress(raw)
            except Exception:
                data = raw

            for line in data.decode("utf-8", errors="replace").strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    continue

                title = doc.get("title", "").strip()
                text_parts = doc.get("text", [])

                # Find the first paragraph with sufficient length
                paragraph = ""
                for part in text_parts:
                    # text can be a list of lists or a list of strings
                    if isinstance(part, list):
                        part = " ".join(str(s) for s in part)
                    part = str(part).strip()
                    if len(part) > MIN_PARAGRAPH_LEN:
                        paragraph = part
                        break

                if not paragraph:
                    continue

                passage = f"{title}. {paragraph}" if title else paragraph
                # Normalize whitespace: replace tabs/newlines with spaces
                passage = " ".join(passage.split())
                passages.append(passage)

                count += 1
                if count % 100_000 == 0:
                    print(f"  Processed {count:,} passages...", flush=True)

    return passages


def main() -> None:
    print(f"Reading abstracts from {ABSTRACTS_TAR}")
    if not os.path.exists(ABSTRACTS_TAR):
        print(f"ERROR: {ABSTRACTS_TAR} not found", file=sys.stderr)
        sys.exit(1)

    passages = extract_passages(ABSTRACTS_TAR)
    print(f"Extracted {len(passages):,} passages total.")

    print(f"Writing {OUTPUT_TSV}")
    with open(OUTPUT_TSV, "w", encoding="utf-8") as out:
        for pid, passage in enumerate(passages):
            out.write(f"{pid}\t{passage}\n")

    size_mb = os.path.getsize(OUTPUT_TSV) / (1024 * 1024)
    print(f"Done. {OUTPUT_TSV} is {size_mb:.1f} MB with {len(passages):,} passages.")


if __name__ == "__main__":
    main()
