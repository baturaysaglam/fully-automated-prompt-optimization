# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from tenants.hotpotqa.code.scorers.normalize import get_tokens, normalize_answer


def test_normalize_lowercase() -> None:
    assert normalize_answer("The DOG") == "dog"


def test_normalize_articles() -> None:
    assert normalize_answer("a cat in the hat") == "cat in hat"


def test_normalize_punctuation() -> None:
    assert normalize_answer("hello, world!") == "hello world"


def test_normalize_whitespace() -> None:
    assert normalize_answer("  too   many  spaces  ") == "too many spaces"


def test_normalize_combined() -> None:
    """All transformations applied together."""
    assert normalize_answer("  The DOG's, a Bone!  ") == "dogs bone"


def test_normalize_empty_string() -> None:
    assert normalize_answer("") == ""


def test_normalize_only_punctuation() -> None:
    assert normalize_answer("!@#$%") == ""


def test_normalize_only_articles() -> None:
    assert normalize_answer("a an the") == ""


def test_get_tokens() -> None:
    assert get_tokens("the big brown dog") == ["big", "brown", "dog"]


def test_get_tokens_empty() -> None:
    assert get_tokens("") == []


def test_get_tokens_only_articles() -> None:
    assert get_tokens("a an the") == []
