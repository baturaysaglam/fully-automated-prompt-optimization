# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from .base import ProviderClient

DEFAULT_MODEL = "bedrock/google.gemma-3-12b-it"
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_MAX_RETRIES = 10
DEFAULT_RETRY_BACKOFF_SECONDS = 5


class LiteLLMClient(ProviderClient):
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: int = DEFAULT_RETRY_BACKOFF_SECONDS,
        temperature: float = 0.0,
        top_p: Optional[float] = None,
        max_tokens: int = 16000,
        completion_fn: Optional[Callable[..., Any]] = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self._completion_fn = completion_fn
        self._sleep_fn = sleep_fn

    def _get_completion_fn(self) -> Callable[..., Any]:
        if self._completion_fn is None:
            import litellm

            self._completion_fn = litellm.completion
        return self._completion_fn

    def generate(self, messages: List[Dict[str, str]]) -> str:
        completion_fn = self._get_completion_fn()
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                kwargs: Dict[str, Any] = dict(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    timeout=self.timeout_seconds,
                    stream=False,
                )
                if self.top_p is not None:
                    kwargs["top_p"] = self.top_p
                response = completion_fn(**kwargs)
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

        raise RuntimeError("LiteLLM call failed after retries") from last_error


def build_litellm_client(settings: Dict[str, object]) -> LiteLLMClient:
    return LiteLLMClient(
        model=str(settings.get("model", DEFAULT_MODEL)),
        timeout_seconds=int(settings.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
        max_retries=int(settings.get("max_retries", DEFAULT_MAX_RETRIES)),
        retry_backoff_seconds=int(
            settings.get("retry_backoff_seconds", DEFAULT_RETRY_BACKOFF_SECONDS)
        ),
        temperature=float(settings.get("temperature", 0.0)),
        top_p=float(settings["top_p"]) if "top_p" in settings else None,
        max_tokens=int(settings.get("max_tokens", 16000)),
    )
