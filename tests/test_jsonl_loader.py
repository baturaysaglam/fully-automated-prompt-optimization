# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from src.hephaestus.datasets.jsonl_loader import load_cases


def test_load_cases_valid_jsonl(tmp_path: Path):
    path = tmp_path / "cases.jsonl"
    path.write_text(
        '{"case_id":"c1","task_type":"x","context":{},"expected":{"label":"malicious"},"metadata":{}}\n',
        encoding="utf-8",
    )

    cases = load_cases(path)
    assert len(cases) == 1
    assert cases[0].case_id == "c1"
    assert cases[0].expected["label"] == "malicious"


def test_load_cases_rejects_missing_required_key(tmp_path: Path):
    path = tmp_path / "cases.jsonl"
    path.write_text('{"case_id":"c1"}\n', encoding="utf-8")

    with pytest.raises(ValueError):
        load_cases(path)


def test_load_cases_accepts_expected_without_label(tmp_path: Path):
    path = tmp_path / "cases.jsonl"
    path.write_text(
        '{"case_id":"c1","task_type":"x","context":{},'
        '"expected":{"rubric":"structured_output"},"metadata":{}}\n',
        encoding="utf-8",
    )

    cases = load_cases(path)
    assert cases[0].expected["rubric"] == "structured_output"
