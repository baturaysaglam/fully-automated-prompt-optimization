# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import io
import json
from urllib import error

import pytest

from src.hephaestus.providers.sagemaker import SagemakerClient


class DummyResponse:
    def __init__(self, payload: str):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_sagemaker_client_generate_sends_expected_request(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("X_API_KEY", "secret-key")
    captured = {}

    def fake_urlopen(req, timeout):  # noqa: ANN001
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(req.header_items())
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        body = {"choices": [{"message": {"content": "ok"}}]}
        return DummyResponse(json.dumps(body))

    provider = SagemakerClient(
        api_url="https://example.execute-api.us-west-2.amazonaws.com/prod/invoke",
        temperature=0.1,
        top_p=0.9,
        max_tokens=42,
        urlopen_fn=fake_urlopen,
    )

    result = provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert result == "ok"
    assert captured["url"] == "https://example.execute-api.us-west-2.amazonaws.com/prod/invoke"
    assert captured["timeout"] == 300
    assert captured["headers"]["X-api-key"] == "secret-key"
    assert captured["headers"]["Content-type"] == "application/json"
    assert captured["payload"]["messages"] == [{"role": "user", "content": "hello"}]
    assert captured["payload"]["temperature"] == 0.1
    assert captured["payload"]["top_p"] == 0.9
    assert captured["payload"]["max_tokens"] == 42


def test_sagemaker_client_generate_falls_back_to_choice_text(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("X_API_KEY", "secret-key")

    def fake_urlopen(_req, timeout):  # noqa: ANN001
        body = {"choices": [{"text": "text output"}]}
        return DummyResponse(json.dumps(body))

    provider = SagemakerClient(urlopen_fn=fake_urlopen)
    result = provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert result == "text output"


def test_sagemaker_client_generate_retries_on_transient_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("X_API_KEY", "secret-key")
    calls = {"count": 0}
    sleeps = []

    def fake_urlopen(_req, timeout):  # noqa: ANN001
        calls["count"] += 1
        if calls["count"] == 1:
            raise error.URLError("temporary failure")
        body = {"content": "top-level content"}
        return DummyResponse(json.dumps(body))

    provider = SagemakerClient(
        max_retries=1,
        retry_backoff_seconds=3,
        urlopen_fn=fake_urlopen,
        sleep_fn=sleeps.append,
    )

    result = provider.generate(messages=[{"role": "user", "content": "hello"}])

    assert result == "top-level content"
    assert calls["count"] == 2
    assert sleeps == [3]


def test_sagemaker_client_generate_raises_when_api_key_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("X_API_KEY", raising=False)
    provider = SagemakerClient()

    with pytest.raises(RuntimeError, match="X_API_KEY is not set"):
        provider.generate(messages=[{"role": "user", "content": "hello"}])


def test_sagemaker_client_generate_raises_after_retries(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("X_API_KEY", "secret-key")

    def fake_urlopen(_req, timeout):  # noqa: ANN001
        raise error.HTTPError(
            url="https://example.invalid/invoke",
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"boom"}'),
        )

    provider = SagemakerClient(max_retries=0, urlopen_fn=fake_urlopen)

    with pytest.raises(RuntimeError, match="Sagemaker call failed after retries"):
        provider.generate(messages=[{"role": "user", "content": "hello"}])
