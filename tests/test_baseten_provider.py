# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import pytest
from helpers import DummyClient, DummyCompletions

from src.hephaestus.providers.baseten import BasetenClient


def test_baseten_client_generate_uses_expected_params():
    completions = DummyCompletions()
    client = DummyClient(completions)
    provider = BasetenClient(client=client)

    result = provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert result == "ok"
    assert completions.called_with["model"] == "/model"
    assert completions.called_with["max_tokens"] == 16000
    assert completions.called_with["temperature"] == 0.0
    assert completions.called_with["top_p"] == 0.95


def test_baseten_client_generate_normalizes_null_content_to_empty_string():
    completions = DummyCompletions()
    client = DummyClient(completions)
    provider = BasetenClient(client=client)

    completions.create = lambda **kwargs: SimpleNamespace(  # type: ignore[method-assign]
        choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
    )
    result = provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert result == ""


def test_baseten_client_raises_when_api_key_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    provider = BasetenClient()
    with pytest.raises(RuntimeError, match="BASETEN_API_KEY is not set"):
        provider.generate(messages=[{"role": "user", "content": "hello"}])
