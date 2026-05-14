# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Chain factory loader for tenant-defined LangGraph chains."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from src.hephaestus.loader import _load_module
from src.hephaestus.providers.base import ProviderClient


def load_chain_factory(
    chain_path: str,
    fn_name: str = "build_chain",
) -> Callable[[ProviderClient, Dict[str, Any]], Any]:
    """Load a chain factory function from a .py file.

    The function must accept (provider: ProviderClient, config: Dict) and return
    a compiled LangGraph StateGraph.

    Args:
        chain_path: Path to the chain Python module.
        fn_name: Name of the factory function to extract (default: "build_chain").

    Returns:
        The factory callable.

    Raises:
        FileNotFoundError: If the chain file does not exist.
        ValueError: If the function is not found or not callable.
    """
    module = _load_module(Path(chain_path))

    attr = getattr(module, fn_name, None)
    if attr is None:
        raise ValueError(
            f"Chain factory function '{fn_name}' not found in {chain_path}"
        )
    if not callable(attr):
        raise ValueError(
            f"'{fn_name}' in {chain_path} is not callable"
        )
    return attr  # type: ignore[return-value]
