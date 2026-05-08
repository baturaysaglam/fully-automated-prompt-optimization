# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests that ifbench configs reference existing prompts and scorer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"
REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("config_name", ["local-chain-variant001.json", "remote-chain-variant001.json"])
def test_config_loads_and_references_valid_paths(config_name: str) -> None:
    cfg = json.loads((CONFIG_DIR / config_name).read_text(encoding="utf-8"))
    assert cfg["tenant_id"] == "ifbench"
    assert cfg["provider_settings"]["temperature"] == 1.0
    assert cfg["provider_settings"]["top_p"] == 0.95

    chain = cfg["chain"]
    assert (REPO_ROOT / chain["path"]).exists()
    for _, prompt_path in chain["config"]["prompt_paths"].items():
        assert (REPO_ROOT / prompt_path).exists()

    scorer_path = cfg["scoring_profile"]["scorer"]["module_path"]
    assert (REPO_ROOT / scorer_path).exists()
