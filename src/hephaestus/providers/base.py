# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class ProviderClient(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]]) -> str:
        raise NotImplementedError
