# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for experiment manifest schema and operations."""

from __future__ import annotations

import json
from pathlib import Path

from src.hephaestus.experiment.manifest import (
    AgentInvocation,
    ExperimentManifest,
    build_manifest,
    load_manifest,
    parse_round_file,
    summarize_invocations,
    write_manifest,
)


def test_parse_round_file_extracts_agent_calls(tmp_path: Path):
    """Correctly counts Agent tool_use events in stream-json."""
    events = [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "Agent", "input": {
                        "subagent_type": "step-attribution",
                        "prompt": "Analyze failures...",
                    }},
                ],
            },
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "Agent", "input": {
                        "subagent_type": "variant-reviewer",
                        "prompt": "Review variant...",
                    }},
                ],
            },
        },
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Done."},
                ],
            },
        },
    ]
    round_file = tmp_path / "round-001.json"
    round_file.write_text(
        "\n".join(json.dumps(e) for e in events),
        encoding="utf-8",
    )

    invocations = parse_round_file(round_file, round_number=1)

    assert len(invocations) == 3  # 1 orchestrator + 2 subagents
    names = [i.agent_name for i in invocations]
    assert "optimization" in names
    assert "step-attribution" in names
    assert "variant-reviewer" in names
    assert all(i.round_number == 1 for i in invocations)


def test_parse_round_file_handles_empty(tmp_path: Path):
    """Empty round file → only the orchestrator invocation."""
    round_file = tmp_path / "round-001.json"
    round_file.write_text("", encoding="utf-8")

    invocations = parse_round_file(round_file, round_number=1)

    assert len(invocations) == 1
    assert invocations[0].agent_name == "optimization"


def test_parse_round_file_handles_malformed(tmp_path: Path):
    """Malformed JSON lines are skipped gracefully."""
    round_file = tmp_path / "round-001.json"
    round_file.write_text("not valid json\n{broken", encoding="utf-8")

    invocations = parse_round_file(round_file, round_number=1)

    assert len(invocations) == 1
    assert invocations[0].agent_name == "optimization"


def test_parse_round_file_nonexistent(tmp_path: Path):
    """Non-existent file → only orchestrator invocation."""
    invocations = parse_round_file(tmp_path / "missing.json", round_number=1)

    assert len(invocations) == 1
    assert invocations[0].agent_name == "optimization"


def test_summarize_invocations_by_agent():
    """Summary correctly aggregates by agent name."""
    invocations = [
        AgentInvocation("optimization", "opus", 1),
        AgentInvocation("step-attribution", "sonnet", 1),
        AgentInvocation("variant-reviewer", "opus", 1),
        AgentInvocation("optimization", "opus", 2),
        AgentInvocation("step-attribution", "sonnet", 2),
    ]

    summary = summarize_invocations(invocations)

    assert summary["total_agent_calls"] == 5
    assert summary["by_agent"]["optimization"] == 2
    assert summary["by_agent"]["step-attribution"] == 2
    assert summary["by_agent"]["variant-reviewer"] == 1


def test_summarize_invocations_by_model():
    """Summary correctly aggregates by model."""
    invocations = [
        AgentInvocation("optimization", "opus", 1),
        AgentInvocation("step-attribution", "sonnet", 1),
        AgentInvocation("variant-reviewer", "opus", 1),
    ]

    summary = summarize_invocations(invocations)

    assert summary["by_model"]["opus"] == 2
    assert summary["by_model"]["sonnet"] == 1


def test_summarize_empty_invocations():
    """Empty invocation list → valid summary with zeros."""
    summary = summarize_invocations([])

    assert summary["total_agent_calls"] == 0
    assert summary["by_agent"] == {}
    assert summary["by_model"] == {}


def test_build_manifest_from_log_dir(tmp_path: Path):
    """End-to-end assembly from sample round files."""
    log_dir = tmp_path / "log"
    log_dir.mkdir()

    events_r1 = [
        {
            "type": "assistant",
            "message": {"content": [
                {"type": "tool_use", "name": "Agent", "input": {
                    "subagent_type": "step-attribution",
                    "prompt": "Analyze...",
                }},
            ]},
        },
    ]
    events_r2 = [
        {
            "type": "assistant",
            "message": {"content": [
                {"type": "tool_use", "name": "Agent", "input": {
                    "subagent_type": "variant-reviewer",
                    "prompt": "Review...",
                }},
            ]},
        },
        {
            "type": "assistant",
            "message": {"content": [
                {"type": "tool_use", "name": "Agent", "input": {
                    "subagent_type": "step-attribution",
                    "prompt": "Analyze again...",
                }},
            ]},
        },
    ]

    (log_dir / "round-001.json").write_text(
        "\n".join(json.dumps(e) for e in events_r1), encoding="utf-8"
    )
    (log_dir / "round-002.json").write_text(
        "\n".join(json.dumps(e) for e in events_r2), encoding="utf-8"
    )

    manifest = build_manifest(
        log_dir=log_dir,
        tenant_id="hotpotqa",
        task_model="gpt-4.1-mini",
        started_at="2026-05-12T10:00:00+00:00",
        completed_at="2026-05-12T10:30:00+00:00",
        duration_seconds=1800.0,
        status="success",
        total_rounds=2,
    )

    assert manifest.tenant_id == "hotpotqa"
    assert manifest.task_model == "gpt-4.1-mini"
    assert manifest.total_rounds == 2
    assert manifest.duration_seconds == 1800.0
    assert manifest.status == "success"
    assert manifest.agent_summary["total_agent_calls"] == 5  # 2 orchestrator + 1 + 2 subagent
    assert manifest.agent_summary["by_agent"]["optimization"] == 2
    assert manifest.agent_summary["by_agent"]["step-attribution"] == 2
    assert manifest.agent_summary["by_agent"]["variant-reviewer"] == 1


def test_write_and_load_manifest_roundtrip(tmp_path: Path):
    """Serialization and deserialization preserves all fields."""
    manifest = ExperimentManifest(
        tenant_id="hotpotqa",
        task_model="gpt-4.1-mini",
        started_at="2026-05-12T10:00:00+00:00",
        completed_at="2026-05-12T10:30:00+00:00",
        duration_seconds=1800.0,
        total_rounds=3,
        agent_invocations=[
            AgentInvocation("optimization", "opus", 1),
            AgentInvocation("step-attribution", "sonnet", 1),
        ],
        agent_summary={"total_agent_calls": 2, "by_agent": {"optimization": 1, "step-attribution": 1}, "by_model": {"opus": 1, "sonnet": 1}},
        eval_runs=[{"run_id": "hephaestus-hotpotqa-abc123", "composite_score": 72.5}],
        final_metrics={"em": 72.67, "f1": 78.84},
        status="success",
    )

    path = tmp_path / "manifest.json"
    write_manifest(manifest, path)

    loaded = load_manifest(path)

    assert loaded.tenant_id == manifest.tenant_id
    assert loaded.task_model == manifest.task_model
    assert loaded.duration_seconds == manifest.duration_seconds
    assert loaded.total_rounds == manifest.total_rounds
    assert loaded.status == manifest.status
    assert loaded.final_metrics == manifest.final_metrics
    assert loaded.eval_runs == manifest.eval_runs
    assert len(loaded.agent_invocations) == 2
    assert loaded.agent_invocations[0].agent_name == "optimization"
    assert loaded.agent_invocations[1].model == "sonnet"
    assert loaded.agent_summary == manifest.agent_summary
