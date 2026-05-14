# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Dict

from .base import ProviderClient
from .baseten import build_baseten_client
from .openai import build_openai_client
from .sagemaker import build_sagemaker_client


def build_provider_client(provider_name: str, settings: Dict[str, object]) -> ProviderClient:
    provider = provider_name.strip().lower()
    if provider in {"baseten", "base10"}:
        return build_baseten_client(settings)
    if provider == "sagemaker":
        return build_sagemaker_client(settings)
    if provider == "openai":
        return build_openai_client(settings)
    raise ValueError(f"Unsupported provider '{provider_name}'")
