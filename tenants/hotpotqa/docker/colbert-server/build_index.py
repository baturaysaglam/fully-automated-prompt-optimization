#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Build a ColBERTv2 index from collection.tsv.

Expects:
  - /data/colbertv2.0/  (extracted checkpoint)
  - /data/collection.tsv

Produces:
  - /data/index/
"""
from __future__ import annotations

import os
import shutil
import sys

CHECKPOINT_DIR = os.environ.get("CHECKPOINT_DIR", "/data/colbertv2.0")
COLLECTION_TSV = os.environ.get("COLLECTION_TSV", "/data/collection.tsv")
INDEX_ROOT = os.environ.get("INDEX_ROOT", "/data")
INDEX_NAME = os.environ.get("INDEX_NAME", "index")


def main() -> None:
    if not os.path.isdir(CHECKPOINT_DIR):
        print(f"ERROR: Checkpoint not found at {CHECKPOINT_DIR}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(COLLECTION_TSV):
        print(f"ERROR: Collection not found at {COLLECTION_TSV}", file=sys.stderr)
        sys.exit(1)

    from colbert import Indexer  # type: ignore[import-untyped]
    from colbert.infra import ColBERTConfig, Run, RunConfig  # type: ignore[import-untyped]

    print(f"Building index from {COLLECTION_TSV} using checkpoint {CHECKPOINT_DIR}")
    print(f"Index will be written under {INDEX_ROOT}")

    with Run().context(RunConfig(nranks=1, root=INDEX_ROOT)):
        config = ColBERTConfig(nbits=2, root=INDEX_ROOT)
        indexer = Indexer(checkpoint=CHECKPOINT_DIR, config=config)
        indexer.index(name=INDEX_NAME, collection=COLLECTION_TSV)

    # ColBERT puts the index under <root>/<experiment>/indexes/<name>/
    # (or <root>/experiments/<experiment>/indexes/<name>/ depending on config).
    # Move it to /data/index/ for the runtime image.
    target = os.path.join(INDEX_ROOT, "index")
    candidates = [
        os.path.join(INDEX_ROOT, "default", "indexes", INDEX_NAME),
        os.path.join(INDEX_ROOT, "experiments", "default", "indexes", INDEX_NAME),
    ]
    generated = next((p for p in candidates if os.path.isdir(p)), None)

    if generated:
        if os.path.isdir(target) and target != generated:
            shutil.rmtree(target)
        shutil.move(generated, target)
        print(f"Moved index from {generated} to {target}")
    elif os.path.isdir(target):
        print(f"Index already at {target}")
    else:
        print(f"WARNING: Could not find generated index in any of: {candidates}", file=sys.stderr)
        sys.exit(1)

    # Clean up ColBERT's output directories
    for cleanup_dir in ["experiments", "default"]:
        d = os.path.join(INDEX_ROOT, cleanup_dir)
        if os.path.isdir(d):
            shutil.rmtree(d)

    print("Index build complete.")


if __name__ == "__main__":
    main()
