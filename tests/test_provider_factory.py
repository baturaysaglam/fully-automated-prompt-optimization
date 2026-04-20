# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from src.hephaestus.providers import build_provider_client
from src.hephaestus.providers.baseten import BasetenClient
from src.hephaestus.providers.openai import OpenAIClient
from src.hephaestus.providers.sagemaker import SagemakerClient


def test_provider_factory_routes_baseten_aliases():
    assert isinstance(build_provider_client("baseten", {}), BasetenClient)
    assert isinstance(build_provider_client("base10", {}), BasetenClient)


def test_provider_factory_routes_sagemaker():
    assert isinstance(build_provider_client("sagemaker", {}), SagemakerClient)


def test_provider_factory_routes_openai():
    assert isinstance(build_provider_client("openai", {}), OpenAIClient)


def test_provider_factory_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported provider"):
        build_provider_client("unknown", {})
