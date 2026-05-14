# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Canonical run ID generation and validation for Hephaestus eval runs."""

from __future__ import annotations

import re
import time

_RUN_ID_PATTERN = re.compile(r"^hephaestus-[a-z0-9_-]+-[a-z0-9]+$")


def _base36(n: int) -> str:
    """Encode a non-negative integer in base-36 (lowercase)."""
    if n == 0:
        return "0"
    digits = []
    while n:
        digits.append("0123456789abcdefghijklmnopqrstuvwxyz"[n % 36])
        n //= 36
    return "".join(reversed(digits))


def generate_run_id(tenant_id: str) -> str:
    """Return ``hephaestus-<tenant_id>-<hash>`` where hash is base36(epoch seconds).

    Underscores in *tenant_id* are replaced with hyphens so the resulting
    ID is a valid DNS / K8s resource name.
    """
    sanitized = tenant_id.replace("_", "-")
    ts_hash = _base36(int(time.time()))
    return f"hephaestus-{sanitized}-{ts_hash}"


def validate_run_id(run_id: str) -> None:
    """Raise ``ValueError`` if *run_id* doesn't match the canonical format."""
    if not _RUN_ID_PATTERN.match(run_id):
        raise ValueError(
            f"Invalid run_id '{run_id}'. "
            "Expected format: hephaestus-<tenant_id>-<hash> "
            "(lowercase alphanumeric, underscores allowed in tenant_id)."
        )
