# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, List, Optional

from .base import ProviderClient

DEFAULT_MODEL = "gpt-4o"
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_MAX_RETRIES = 10
DEFAULT_RETRY_BACKOFF_SECONDS = 5


class OpenAIClient(ProviderClient):
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: int = DEFAULT_RETRY_BACKOFF_SECONDS,
        temperature: float = 0.0,
        top_p: Optional[float] = None,
        max_tokens: int = 16000,
        client: Optional[Any] = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
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

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        return OpenAI(
            api_key=api_key,
            timeout=self.timeout_seconds,
        )

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = self._create_client()
        return self._client

    @property
    def _is_reasoning_model(self) -> bool:
        """Check if this is a reasoning model that needs special API params.

        These models don't support temperature/top_p, require
        max_completion_tokens, and o-series models need developer role.
        """
        model_lower = self.model.lower()
        if any(model_lower.startswith(prefix) for prefix in ("o1", "o3", "o4")):
            return True
        if any(model_lower.startswith(prefix) for prefix in ("gpt-5", "gpt5")):
            return True
        return False

    def generate(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                # Reasoning models (o-series, GPT-5) use different API parameters
                if self._is_reasoning_model:
                    # Reasoning models: no temperature/top_p, use
                    # max_completion_tokens, and require developer role
                    # instead of system role.
                    adapted = []
                    for m in messages:
                        if m.get("role") == "system":
                            adapted.append({"role": "developer", "content": m["content"]})
                        else:
                            adapted.append(m)
                    response = client.chat.completions.create(
                        model=self.model,
                        messages=adapted,
                        max_completion_tokens=self.max_tokens,
                        n=1,
                        stream=False,
                    )
                else:
                    kwargs: Dict[str, Any] = dict(
                        model=self.model,
                        messages=messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        n=1,
                        stream=False,
                    )
                    if self.top_p is not None:
                        kwargs["top_p"] = self.top_p
                    response = client.chat.completions.create(**kwargs)
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

        raise RuntimeError("OpenAI call failed after retries") from last_error


def build_openai_client(settings: Dict[str, object]) -> OpenAIClient:
    return OpenAIClient(
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
