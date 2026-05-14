# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import time
import warnings
from typing import Any, Callable, Dict, List, Optional
from urllib import error, request

from .base import ProviderClient

DEFAULT_API_URL = (
    "https://your-api-gateway.execute-api.us-west-2.amazonaws.com/prod/models/instruct-16k/invoke"
)
DEFAULT_API_KEY_ENV = "X_API_KEY"
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_MAX_RETRIES = 10
DEFAULT_RETRY_BACKOFF_SECONDS = 5


class SagemakerClient(ProviderClient):
    def __init__(
        self,
        api_url: str = DEFAULT_API_URL,
        api_key_env: str = DEFAULT_API_KEY_ENV,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: int = DEFAULT_RETRY_BACKOFF_SECONDS,
        temperature: float = 0.0,
        top_p: float = 0.95,
        max_tokens: int = 16000,
        urlopen_fn: Callable[..., Any] = request.urlopen,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        self.api_url = api_url
        self.api_key_env = api_key_env
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self._urlopen_fn = urlopen_fn
        self._sleep_fn = sleep_fn

    def _extract_output_text(self, body: Any) -> str:
        if not isinstance(body, dict):
            return ""

        choices = body.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
                text = first_choice.get("text")
                if isinstance(text, str):
                    return text

        content = body.get("content")
        if isinstance(content, str):
            return content

        return ""

    def generate(self, messages: List[Dict[str, str]]) -> str:
        if self.api_url == DEFAULT_API_URL:
            warnings.warn(
                "Using default Sagemaker URL. "
                "Set provider_settings.api_url in your eval config for your deployment.",
                stacklevel=2,
            )
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"{self.api_key_env} is not set.")

        payload = json.dumps(
            {
                "messages": messages,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_tokens": self.max_tokens,
            }
        ).encode("utf-8")

        req = request.Request(
            self.api_url,
            data=payload,
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            method="POST",
        )

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                with self._urlopen_fn(req, timeout=self.timeout_seconds) as resp:
                    raw_body = resp.read().decode("utf-8")
                body = json.loads(raw_body)
                output_text = self._extract_output_text(body)
                if output_text:
                    return output_text
                return json.dumps(body, indent=2, ensure_ascii=False)
            except error.HTTPError as exc:
                details = exc.read().decode("utf-8", errors="replace")
                last_error = RuntimeError(
                    f"HTTP {exc.code} calling invoke endpoint: {details}"
                )
            except error.URLError as exc:
                last_error = RuntimeError(f"Network error calling invoke endpoint: {exc}")
            except Exception as exc:  # noqa: BLE001
                last_error = exc

            if attempt < self.max_retries:
                self._sleep_fn(self.retry_backoff_seconds)

        raise RuntimeError("Sagemaker call failed after retries") from last_error


def build_sagemaker_client(settings: Dict[str, object]) -> SagemakerClient:
    return SagemakerClient(
        api_url=str(settings.get("api_url", DEFAULT_API_URL)),
        api_key_env=str(settings.get("api_key_env", DEFAULT_API_KEY_ENV)),
        timeout_seconds=int(settings.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
        max_retries=int(settings.get("max_retries", DEFAULT_MAX_RETRIES)),
        retry_backoff_seconds=int(
            settings.get("retry_backoff_seconds", DEFAULT_RETRY_BACKOFF_SECONDS)
        ),
        temperature=float(settings.get("temperature", 0.0)),
        top_p=float(settings.get("top_p", 0.95)),
        max_tokens=int(settings.get("max_tokens", 16000)),
    )
