#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Local HTTP server wrapping ColBERTv2 Searcher for HotpotQA retrieval."""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

DEFAULT_DATA_DIR = Path("tenants/hotpotqa/data/colbert_index")
DEFAULT_PORT = 8893


class ColBERTHandler(BaseHTTPRequestHandler):
    """HTTP request handler that delegates search to a ColBERT Searcher."""

    searcher: Any = None  # Assigned before server starts.

    def do_GET(self) -> None:
        """Handle GET /?query=...&k=3 requests."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        query = params.get("query", [None])[0]  # type: ignore[arg-type]
        if not query:
            self._send_json(400, {"error": "Missing required 'query' parameter"})
            return

        try:
            k = int(params.get("k", ["3"])[0])
        except ValueError:
            self._send_json(400, {"error": "'k' must be an integer"})
            return
        if k < 1:
            self._send_json(400, {"error": "'k' must be a positive integer"})
            return

        try:
            pids, _ranks, scores = self.searcher.search(query, k=k)
            passages: list[str] = []
            for pid in pids:
                passages.append(self.searcher.collection[pid])

            self._send_json(
                200,
                {
                    "query": query,
                    "k": k,
                    "passages": passages,
                    "scores": [float(s) for s in scores],
                },
            )
        except Exception as exc:
            self._send_json(500, {"error": f"Search failed: {exc}"})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        """Send a JSON response with the given HTTP status."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Log to stderr with a [ColBERT] prefix."""
        sys.stderr.write(f"[ColBERT] {format % args}\n")


def start_server(data_dir: Path, port: int) -> None:
    """Load the ColBERT index and start the HTTP server.

    Args:
        data_dir: Directory containing the ``index/`` subdirectory and
            ``collection.tsv``.
        port: TCP port to listen on.
    """
    # Late import so the module can be imported without colbert-ai installed.
    from colbert import Searcher  # type: ignore[import-untyped]
    from colbert.infra import Run, RunConfig  # type: ignore[import-untyped]

    index_dir = data_dir / "index"
    collection_path = data_dir / "collection.tsv"

    if not index_dir.exists():
        print(f"Error: Index not found at {index_dir}", file=sys.stderr)
        print("Ensure the index has been built and DATA_DIR is set correctly.", file=sys.stderr)
        sys.exit(1)

    if not collection_path.exists():
        print(f"Error: Collection not found at {collection_path}", file=sys.stderr)
        print("Ensure collection.tsv has been built and DATA_DIR is set correctly.", file=sys.stderr)
        sys.exit(1)

    checkpoint = os.environ.get("CHECKPOINT_DIR", "")
    if checkpoint:
        print(f"Loading ColBERT index from {index_dir} (checkpoint: {checkpoint}) ...")
    else:
        print(f"Loading ColBERT index from {index_dir} ...")

    with Run().context(RunConfig(nranks=1)):
        kwargs: dict[str, str] = {
            "index": str(index_dir),
            "collection": str(collection_path),
        }
        if checkpoint:
            kwargs["checkpoint"] = checkpoint
        searcher = Searcher(**kwargs)
    print("Index loaded successfully.")

    ColBERTHandler.searcher = searcher

    server = ThreadingHTTPServer(("", port), ColBERTHandler)
    print(f"Serving on http://localhost:{port}")
    print(f'Try: curl "http://localhost:{port}/?query=capital+of+France&k=3"')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Start local ColBERT search server for HotpotQA retrieval.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing index and collection (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port to serve on (default: %(default)s)",
    )
    args = parser.parse_args()
    start_server(args.data_dir, args.port)


if __name__ == "__main__":
    main()
