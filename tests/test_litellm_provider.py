# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

import pytest

from src.hephaestus.providers.litellm import LiteLLMClient


class DummyCompletion:
    """Callable that mimics litellm.completion() for testing."""

    def __init__(self):
        self.called_with: dict | None = None

    def __call__(self, **kwargs):
        self.called_with = kwargs
        message = SimpleNamespace(content="ok")
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


def test_litellm_client_generate_uses_expected_params():
    completion_fn = DummyCompletion()
    provider = LiteLLMClient(
        model="bedrock/google.gemma-3-12b-it",
        completion_fn=completion_fn,
    )

    result = provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert result == "ok"
    assert completion_fn.called_with["model"] == "bedrock/google.gemma-3-12b-it"
    assert completion_fn.called_with["max_tokens"] == 16000
    assert completion_fn.called_with["temperature"] == 0.0
    assert completion_fn.called_with["timeout"] == 300
    assert completion_fn.called_with["stream"] is False
    assert "top_p" not in completion_fn.called_with


def test_litellm_client_generate_passes_top_p_when_set():
    completion_fn = DummyCompletion()
    provider = LiteLLMClient(
        model="openai/gpt-4o",
        top_p=0.9,
        completion_fn=completion_fn,
    )

    provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert completion_fn.called_with["top_p"] == 0.9


def test_litellm_client_generate_normalizes_null_content_to_empty_string():
    def null_content_fn(**kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
        )

    provider = LiteLLMClient(completion_fn=null_content_fn)
    result = provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert result == ""


def test_litellm_client_generate_normalizes_missing_message_to_empty_string():
    def no_message_fn(**kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=None)])

    provider = LiteLLMClient(completion_fn=no_message_fn)
    result = provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert result == ""


def test_litellm_client_generate_retries_on_transient_error():
    calls = {"count": 0}
    sleeps = []

    def flaky_fn(**kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ConnectionError("temporary failure")
        message = SimpleNamespace(content="recovered")
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])

    provider = LiteLLMClient(
        max_retries=2,
        retry_backoff_seconds=3,
        completion_fn=flaky_fn,
        sleep_fn=sleeps.append,
    )

    result = provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert result == "recovered"
    assert calls["count"] == 2
    assert sleeps == [3]


def test_litellm_client_generate_raises_after_retries_exhausted():
    def always_fail_fn(**kwargs):
        raise RuntimeError("persistent failure")

    sleeps = []
    provider = LiteLLMClient(
        max_retries=2,
        retry_backoff_seconds=1,
        completion_fn=always_fail_fn,
        sleep_fn=sleeps.append,
    )

    with pytest.raises(RuntimeError, match="LiteLLM call failed after retries"):
        provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert len(sleeps) == 2


def test_litellm_client_generate_no_retry_when_max_retries_zero():
    def fail_fn(**kwargs):
        raise RuntimeError("boom")

    sleeps = []
    provider = LiteLLMClient(
        max_retries=0,
        completion_fn=fail_fn,
        sleep_fn=sleeps.append,
    )

    with pytest.raises(RuntimeError, match="LiteLLM call failed after retries"):
        provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert sleeps == []


def test_litellm_client_lazy_imports_litellm_when_no_completion_fn(monkeypatch):
    import sys

    monkeypatch.delitem(sys.modules, "litellm", raising=False)
    mock_module = SimpleNamespace(completion=lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "litellm", mock_module)

    provider = LiteLLMClient()
    fn = provider._get_completion_fn()

    assert fn is mock_module.completion
