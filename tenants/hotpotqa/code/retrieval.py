# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""BM25 retrieval module node for the HotpotQA multi-hop chain.

Uses in-process bm25s for passage retrieval instead of an external server.
On first use the Wikipedia abstracts corpus is downloaded from HuggingFace,
tokenized with an English stemmer, and indexed locally.  Subsequent calls
load the pre-built index from disk and use diskcache for query memoization.
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

_retriever: Any = None
_stemmer: Any = None
_corpus: list[str] | None = None
_initialized = False
_init_lock = threading.Lock()


def _initialize_bm25_index(data_dir: str) -> None:
    """Download wiki abstracts corpus from HuggingFace, build BM25 index, and save."""
    from dspy.utils import download

    download("https://huggingface.co/dspy/cache/resolve/main/wiki.abstracts.2017.tar.gz")

    import tarfile

    with tarfile.open("wiki.abstracts.2017.tar.gz", "r:gz") as tar:
        tar.extractall(path=data_dir, filter="data")

    import ujson

    corpus: list[str] = []
    corpus_path = os.path.join(data_dir, "wiki.abstracts.2017.jsonl")
    assert os.path.exists(corpus_path), (
        "Corpus file not found. Please ensure the corpus is downloaded and extracted correctly."
    )

    with open(corpus_path) as f:
        for line in f:
            record = ujson.loads(line)
            corpus.append(f"{record['title']} | {' '.join(record['text'])}")

    import bm25s
    import Stemmer

    stemmer = Stemmer.Stemmer("english")
    corpus_tokens = bm25s.tokenize(corpus, stopwords="en", stemmer=stemmer)

    retriever = bm25s.BM25(k1=0.9, b=0.4)
    retriever.index(corpus_tokens)

    save_dir = os.path.join(data_dir, "bm25s_retriever")
    retriever.save(save_dir)
    assert os.path.exists(save_dir), "Retriever not saved correctly."


def _init_retriever(data_dir: str) -> None:
    """Thread-safe lazy init: load pre-built index or build from scratch."""
    global _retriever, _stemmer, _corpus, _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        index_dir = os.path.join(data_dir, "bm25s_retriever")
        corpus_path = os.path.join(data_dir, "wiki.abstracts.2017.jsonl")
        if not os.path.exists(index_dir) or not os.path.exists(corpus_path):
            logger.info("BM25 index not found at %s — building from scratch...", data_dir)
            os.makedirs(data_dir, exist_ok=True)
            _initialize_bm25_index(data_dir)

        import bm25s
        import Stemmer

        _retriever = bm25s.BM25.load(index_dir)
        _stemmer = Stemmer.Stemmer("english")

        import ujson

        corpus_data: list[str] = []
        with open(corpus_path) as f:
            for line in f:
                record = ujson.loads(line)
                corpus_data.append(f"{record['title']} | {' '.join(record['text'])}")
        _corpus = corpus_data
        _initialized = True
        logger.info("BM25 retriever loaded (%d documents)", len(_corpus))


def _search_bm25(query: str, k: int, data_dir: str) -> list[str]:
    """Tokenize query, retrieve top-k passages from BM25 index, return list of strings.

    Results are memoized with diskcache at ``{data_dir}/retriever_cache/``.
    """
    from diskcache import Cache

    cache = Cache(os.path.join(data_dir, "retriever_cache"))

    cache_key = f"{query}||{k}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    _init_retriever(data_dir)
    import bm25s

    tokens = bm25s.tokenize(query, stopwords="en", stemmer=_stemmer, show_progress=False)
    results, scores = _retriever.retrieve(tokens, k=k, n_threads=1, show_progress=False)  # type: ignore[union-attr]
    passages = [_corpus[doc] for doc, _score in zip(results[0], scores[0])][:k]  # type: ignore[index]

    cache.set(cache_key, passages)
    return passages


def make_retrieval_node(
    query_key: str | None = None,
    data_dir: str = "tenants/hotpotqa/data/bm25",
    k: int = 7,
    output_key: str = "retrieve",
    *,
    context_key: str | None = None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Create a LangGraph node that queries BM25 and writes passages to step_outputs.

    Exactly one of *query_key* or *context_key* must be provided.  When *context_key*
    is set the query is read from ``state["context"][context_key]`` (useful for the
    first hop where no prior LLM output exists).  Otherwise the query is read from
    ``state["step_outputs"][query_key]``.
    """
    if (query_key is None) == (context_key is None):
        raise ValueError("Exactly one of query_key or context_key must be provided")

    def node(state: dict[str, Any]) -> dict[str, Any]:
        step_outputs = dict(state.get("step_outputs", {}))
        if context_key is not None:
            query = state["context"][context_key]
        else:
            query = step_outputs[query_key]
        passages = _search_bm25(query, k, data_dir)
        step_outputs[output_key] = "\n".join(
            f"[{i}] \u00ab{p}\u00bb" for i, p in enumerate(passages, 1)
        )
        return {"step_outputs": step_outputs}

    return node
