#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Local HTTP retrieval server using Wikipedia API as backend.

Drop-in replacement for the ColBERT server when the ColBERTv2 index is
unavailable.  Serves the same ``GET /?query=...&k=3`` interface and returns
the same ``{"passages": [...]}`` JSON format.

Usage:
    python tenants/hotpotqa/scripts/start_wiki_retrieval_server.py [--port 8893]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

DEFAULT_PORT = 8893
USER_AGENT = "HephaestusRetrievalBot/1.0 (hotpotqa-eval)"


def _clean_query(query: str) -> str:
    """Strip boolean operators and quotes that Wikipedia search doesn't handle."""
    # Remove quoted phrases — keep the words inside
    query = query.replace('"', "")
    # Remove boolean operators
    query = re.sub(r"\b(AND|OR|NOT)\b", " ", query)
    # Collapse whitespace
    return re.sub(r"\s+", " ", query).strip()


def _wiki_search(query: str, k: int) -> list[str]:
    """Run a single Wikipedia search API call and return matching titles."""
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": k,
            "format": "json",
        }
    )
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def _search_wikipedia(query: str, k: int = 3) -> list[str]:
    """Search Wikipedia full-text and return up to *k* page abstracts.

    Falls back to progressively shorter queries if the full query returns
    no results (Wikipedia search handles simple entity names better than
    multi-attribute queries).
    """
    query = _clean_query(query)
    titles = _wiki_search(query, k)

    # Fallback: try progressively shorter queries
    if not titles:
        words = query.split()
        for end in range(len(words) - 1, 0, -1):
            shorter = " ".join(words[:end])
            titles = _wiki_search(shorter, k)
            if titles:
                break

    if not titles:
        return []

    return _get_extracts(titles)


def _get_extracts(titles: list[str]) -> list[str]:
    """Batch-fetch page extracts (abstracts) for the given titles."""
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "titles": "|".join(titles),
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "format": "json",
        }
    )
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    pages = data.get("query", {}).get("pages", {})
    # Build a title→extract lookup, then walk the original title order
    title_to_extract: dict[str, str] = {}
    for page in pages.values():
        title = page.get("title", "")
        text = page.get("extract", "").strip()
        if text and title:
            title_to_extract[title] = text
    return [title_to_extract[t] for t in titles if t in title_to_extract]


class WikiRetrievalHandler(BaseHTTPRequestHandler):
    """HTTP handler matching the ColBERT server interface."""

    def do_GET(self) -> None:
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
            passages = _search_wikipedia(query, k=k)
            self._send_json(
                200,
                {
                    "query": query,
                    "k": k,
                    "passages": passages,
                    "scores": [1.0 / (i + 1) for i in range(len(passages))],
                },
            )
        except Exception as exc:
            self._send_json(500, {"error": f"Search failed: {exc}"})

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write(f"[WikiRetrieval] {format % args}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Start local Wikipedia retrieval server (ColBERT API compatible).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port to serve on (default: %(default)s)",
    )
    args = parser.parse_args()

    server = HTTPServer(("", args.port), WikiRetrievalHandler)
    print(f"Wikipedia retrieval server on http://localhost:{args.port}")
    print(f'Try: curl "http://localhost:{args.port}/?query=capital+of+France&k=3"')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
