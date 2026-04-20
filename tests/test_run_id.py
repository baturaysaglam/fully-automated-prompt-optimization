# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import re

import pytest

from src.hephaestus.runs.run_id import generate_run_id, validate_run_id

_RUN_ID_RE = re.compile(r"^hephaestus-[a-z0-9_-]+-[a-z0-9]+$")


def test_generate_run_id_format() -> None:
    run_id = generate_run_id("hotpotqa")
    assert _RUN_ID_RE.match(run_id), f"Bad format: {run_id}"
    assert run_id.startswith("hephaestus-hotpotqa-")


def test_generate_run_id_underscore_tenant() -> None:
    """Underscores in tenant_id are replaced with hyphens for K8s compatibility."""
    run_id = generate_run_id("cti_cwe")
    assert _RUN_ID_RE.match(run_id), f"Bad format: {run_id}"
    assert run_id.startswith("hephaestus-cti-cwe-")


@pytest.mark.parametrize(
    "run_id",
    [
        "hephaestus-hotpotqa-m5kx7r",
        "hephaestus-cti_cwe-abc123",
        "hephaestus-cti-rcm-abc123",
        "hephaestus-demo-0",
    ],
)
def test_validate_run_id_valid(run_id: str) -> None:
    validate_run_id(run_id)  # should not raise


@pytest.mark.parametrize(
    "run_id",
    [
        "",
        "hotpotqa-m5kx7r",  # missing prefix
        "hephaestus--m5kx7r",  # empty tenant
        "hephaestus-HOTPOTQA-m5kx7r",  # uppercase tenant
        "hephaestus-hotpotqa-",  # empty hash
        "hephaestus-hotpotqa-ABC",  # uppercase hash
        "hephaestus-hot potqa-m5kx7r",  # space in tenant
    ],
)
def test_validate_run_id_rejects_invalid(run_id: str) -> None:
    with pytest.raises(ValueError, match="Invalid run_id"):
        validate_run_id(run_id)
