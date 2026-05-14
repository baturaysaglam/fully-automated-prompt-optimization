# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import string
import unicodedata

_PUNCTUATION = set(string.punctuation)


def normalize_answer(text: str) -> str:
    """Normalize answer text to match DSPy's ``normalize_text``.

    Steps: Unicode NFD → lowercase → remove punctuation (set exclusion) →
    remove articles → collapse whitespace.
    """
    text = unicodedata.normalize("NFD", text)
    text = text.lower()
    text = _remove_punctuation(text)
    text = _remove_articles(text)
    text = _collapse_whitespace(text)
    return text


def get_tokens(text: str) -> list[str]:
    """Split normalized text into tokens."""
    normalized = normalize_answer(text)
    if not normalized:
        return []
    return normalized.split()


def _remove_punctuation(text: str) -> str:
    return "".join(ch for ch in text if ch not in _PUNCTUATION)


def _remove_articles(text: str) -> str:
    return re.sub(r"\b(a|an|the)\b", " ", text)


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())
