# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import time
import warnings
from typing import Any, Callable, Dict, List, Optional

from .base import ProviderClient

DEFAULT_MODEL = "/model"
DEFAULT_BASE_URL = "https://your-baseten-model.api.baseten.co/environments/production/sync/v1"
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_MAX_RETRIES = 10
DEFAULT_RETRY_BACKOFF_SECONDS = 5


class BasetenClient(ProviderClient):
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: int = DEFAULT_RETRY_BACKOFF_SECONDS,
        temperature: float = 0.0,
        top_p: float = 0.95,
        max_tokens: int = 16000,
        client: Optional[Any] = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self._client = client
        self._sleep_fn = sleep_fn

    def _create_client(self) -> Any:
        from openai import OpenAI

        if self.base_url == DEFAULT_BASE_URL:
            warnings.warn(
                "Using default Baseten URL. "
                "Set provider_settings.base_url in your eval config for your deployment.",
                stacklevel=2,
            )
        api_key = os.environ.get("BASETEN_API_KEY")
        if not api_key:
            raise RuntimeError("BASETEN_API_KEY is not set.")
        return OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def generate(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    n=1,
                    stream=False,
                )
                choice = response.choices[0]
                if not choice.message:
                    return ""
                content = choice.message.content
                return content if isinstance(content, str) else ""
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.max_retries:
                    break
                self._sleep_fn(self.retry_backoff_seconds)

        raise RuntimeError("Baseten call failed after retries") from last_error


def build_baseten_client(settings: Dict[str, object]) -> BasetenClient:
    return BasetenClient(
        base_url=str(settings.get("base_url", DEFAULT_BASE_URL)),
        model=str(settings.get("model", DEFAULT_MODEL)),
        timeout_seconds=int(settings.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
        max_retries=int(settings.get("max_retries", DEFAULT_MAX_RETRIES)),
        retry_backoff_seconds=int(
            settings.get("retry_backoff_seconds", DEFAULT_RETRY_BACKOFF_SECONDS)
        ),
        temperature=float(settings.get("temperature", 0.0)),
        top_p=float(settings.get("top_p", 0.95)),
        max_tokens=int(settings.get("max_tokens", 16000)),
    )
