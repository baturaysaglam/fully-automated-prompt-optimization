#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

# DEPRECATED: ColBERT retrieval has been replaced by in-process BM25 (bm25s).
# See tenants/hotpotqa/code/retrieval.py for the new implementation.
# This file is kept for reference only.
"""Download and build ColBERTv2 wiki17_abstracts index for HotpotQA retrieval.

The pre-built index and collection.tsv that were previously hosted at
downloads.cs.stanford.edu are no longer available (404). This script
downloads the raw HotpotQA Wikipedia abstracts and builds the collection
and index locally.

Preferred alternative: use the Docker image in
``tenants/hotpotqa/docker/colbert-server/`` which builds everything
during ``docker build``.
"""
from __future__ import annotations

import argparse
import sys
import tarfile
import urllib.request
from pathlib import Path

# Add docker/colbert-server to sys.path so we can reuse its build_collection module.
_DOCKER_DIR = Path(__file__).resolve().parents[1] / "docker" / "colbert-server"
if str(_DOCKER_DIR) not in sys.path:
    sys.path.insert(0, str(_DOCKER_DIR))

from build_collection import extract_passages  # noqa: E402

DEFAULT_DATA_DIR = Path("tenants/hotpotqa/data/colbert_index")

ABSTRACTS_URL = (
    "https://nlp.stanford.edu/projects/hotpotqa/"
    "enwiki-20171001-pages-meta-current-withlinks-abstracts.tar.bz2"
)
CHECKPOINT_URL = (
    "https://downloads.cs.stanford.edu/nlp/data/colbert/colbertv2/"
    "colbertv2.0.tar.gz"
)


def _download_with_progress(url: str, dest: Path) -> None:
    """Download a file with a console progress indicator."""
    print(f"Downloading {url}")
    print(f"  -> {dest}")

    def _reporthook(block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 // total_size)
            mb_done = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(
                f"\r  {pct}% ({mb_done:.1f}/{mb_total:.1f} MB)",
                end="",
                flush=True,
            )
        else:
            mb_done = downloaded / (1024 * 1024)
            print(f"\r  {mb_done:.1f} MB downloaded", end="", flush=True)

    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, str(dest), reporthook=_reporthook)
    print()


def _file_size_str_raw(size_bytes: int) -> str:
    """Return a human-readable size string from a byte count."""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _file_size_str(path: Path) -> str:
    """Return a human-readable file size string."""
    if not path.exists():
        return "not found"
    return _file_size_str_raw(path.stat().st_size)


def _build_collection(abstracts_tar: Path, collection_path: Path) -> None:
    """Parse raw abstracts tarball into a collection.tsv file.

    Delegates to ``build_collection.extract_passages`` from the Docker context
    to avoid duplicating the passage-extraction logic.
    """
    print(f"Building collection from {abstracts_tar}...")
    passages = extract_passages(str(abstracts_tar))

    print(f"Writing {len(passages):,} passages to {collection_path}")
    with open(collection_path, "w", encoding="utf-8") as out:
        for pid, passage in enumerate(passages):
            out.write(f"{pid}\t{passage}\n")

    print(f"Collection built: {_file_size_str(collection_path)}")


def _build_index(data_dir: Path, checkpoint_dir: Path, collection_path: Path) -> None:
    """Build ColBERT index using the Indexer API."""
    import shutil

    from colbert import Indexer  # type: ignore[import-untyped]
    from colbert.infra import ColBERTConfig, Run, RunConfig  # type: ignore[import-untyped]

    index_dir = data_dir / "index"
    print(f"Building ColBERT index from {collection_path}...")

    with Run().context(RunConfig(nranks=1)):
        config = ColBERTConfig(nbits=2, root=str(data_dir))
        indexer = Indexer(checkpoint=str(checkpoint_dir), config=config)
        indexer.index(name="index", collection=str(collection_path))

    generated = data_dir / "experiments" / "default" / "indexes" / "index"
    if generated.is_dir():
        if index_dir.is_dir() and index_dir != generated:
            shutil.rmtree(index_dir)
        shutil.move(str(generated), str(index_dir))

    exp_dir = data_dir / "experiments"
    if exp_dir.is_dir():
        shutil.rmtree(exp_dir)

    print(f"Index built at {index_dir}")


def setup_colbert(data_dir: Path) -> None:
    """Download abstracts, build collection and index.

    Args:
        data_dir: Directory to store the index and collection.
    """
    data_dir.mkdir(parents=True, exist_ok=True)

    # --- Collection ---
    collection_path = data_dir / "collection.tsv"
    if collection_path.exists():
        print(f"Collection already exists: {collection_path}")
    else:
        abstracts_tar = data_dir / "abstracts.tar.bz2"
        if not abstracts_tar.exists():
            _download_with_progress(ABSTRACTS_URL, abstracts_tar)
        _build_collection(abstracts_tar, collection_path)
        abstracts_tar.unlink(missing_ok=True)

    # --- Index ---
    index_dir = data_dir / "index"
    if index_dir.exists() and any(index_dir.iterdir()):
        print(f"Index already exists: {index_dir}")
    else:
        checkpoint_dir = data_dir / "colbertv2.0"
        checkpoint_tar = data_dir / "colbertv2.tar.gz"

        if not checkpoint_dir.exists():
            if not checkpoint_tar.exists():
                _download_with_progress(CHECKPOINT_URL, checkpoint_tar)
            print(f"Extracting checkpoint to {data_dir}...")
            with tarfile.open(checkpoint_tar, "r:gz") as tar:
                tar.extractall(path=str(data_dir), filter="data")
            checkpoint_tar.unlink(missing_ok=True)

        _build_index(data_dir, checkpoint_dir, collection_path)

    # --- Verification ---
    print("\n=== Verification ===")
    print(f"Data directory : {data_dir}")
    print(f"Collection     : {collection_path} ({_file_size_str(collection_path)})")
    print(f"Index directory: {index_dir}")
    if index_dir.exists():
        file_count = 0
        total_size = 0
        for f in index_dir.rglob("*"):
            if f.is_file():
                file_count += 1
                total_size += f.stat().st_size
        print(f"  Files: {file_count}")
        print(f"  Total size: {_file_size_str_raw(total_size)}")
    else:
        print("  WARNING: Index directory not found after build")

    print("\nSetup complete. Start the server with:")
    print(
        f"  python tenants/hotpotqa/scripts/start_colbert_server.py"
        f" --data-dir {data_dir}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download HotpotQA Wikipedia abstracts and build ColBERTv2 index. "
            "Alternatively, use the Docker image in "
            "tenants/hotpotqa/docker/colbert-server/."
        ),
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory to store index and collection (default: %(default)s)",
    )
    args = parser.parse_args()
    setup_colbert(args.data_dir)


if __name__ == "__main__":
    main()
