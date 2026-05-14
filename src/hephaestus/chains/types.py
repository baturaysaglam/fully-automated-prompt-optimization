# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Dict, List, TypedDict


class ChainState(TypedDict, total=False):
    """Base state protocol for Hephaestus chains.

    Required:
        context: Input from case.context — the eval runner populates this
        output_text: Final output — the eval runner reads this for scoring

    Optional:
        step_outputs: Intermediate outputs — pipeline-aware scorers can inspect these
        diagnostics: Generic debug messages that any chain node or tenant code can write to
    """

    context: Dict[str, str]
    output_text: str
    step_outputs: Dict[str, str]
    diagnostics: List[str]
