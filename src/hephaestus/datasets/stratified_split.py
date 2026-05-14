# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Stratified dev/test splitting for evaluation datasets."""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Any, Callable, Dict, List, Tuple


def stratified_split_by_key(
    cases: List[Dict[str, Any]],
    key_fn: Callable[[Dict[str, Any]], str],
    dev_fraction: float = 0.2,
    seed: int = 42,
    rare_threshold: int = 3,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split cases into dev/test, stratified by key_fn(case).

    Groups with <= *rare_threshold* cases go entirely to test to prevent
    overfitting during optimization. Remaining groups are split at
    *dev_fraction*.

    Returns (dev_cases, test_cases).
    """
    rng = random.Random(seed)

    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in cases:
        groups[key_fn(case)].append(case)

    dev: List[Dict[str, Any]] = []
    test: List[Dict[str, Any]] = []

    for key in sorted(groups):
        group = groups[key]
        if len(group) <= rare_threshold:
            test.extend(group)
        else:
            shuffled = list(group)
            rng.shuffle(shuffled)
            split_idx = max(1, int(len(shuffled) * dev_fraction))
            dev.extend(shuffled[:split_idx])
            test.extend(shuffled[split_idx:])

    rng.shuffle(dev)
    rng.shuffle(test)
    return dev, test
