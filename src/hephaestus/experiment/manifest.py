# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

AGENT_MODELS: Dict[str, str] = {
    "optimization": "opus",
    "step-attribution": "sonnet",
    "variant-reviewer": "opus",
    "pr-lifecycle": "opus",
    "k8s-manager": "sonnet",
}


@dataclass
class AgentInvocation:
    agent_name: str
    model: str
    round_number: int


@dataclass
class ExperimentManifest:
    tenant_id: str
    task_model: str
    started_at: str
    completed_at: str
    duration_seconds: float
    total_rounds: int
    agent_invocations: List[AgentInvocation]
    agent_summary: Dict[str, Any]
    eval_runs: List[Dict[str, Any]] = field(default_factory=list)
    final_metrics: Optional[Dict[str, float]] = None
    status: str = "success"


def summarize_invocations(invocations: List[AgentInvocation]) -> Dict[str, Any]:
    by_agent: Dict[str, int] = {}
    by_model: Dict[str, int] = {}
    for inv in invocations:
        by_agent[inv.agent_name] = by_agent.get(inv.agent_name, 0) + 1
        by_model[inv.model] = by_model.get(inv.model, 0) + 1
    return {
        "total_agent_calls": len(invocations),
        "by_agent": by_agent,
        "by_model": by_model,
    }


def parse_round_file(path: Path, round_number: int) -> List[AgentInvocation]:
    invocations: List[AgentInvocation] = []
    # The orchestrator itself counts as one invocation per round
    invocations.append(AgentInvocation(
        agent_name="optimization",
        model=AGENT_MODELS["optimization"],
        round_number=round_number,
    ))
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return invocations

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if evt.get("type") != "assistant":
            continue
        content_blocks = evt.get("message", {}).get("content", [])
        for block in content_blocks:
            if block.get("type") != "tool_use":
                continue
            if block.get("name") != "Agent":
                continue
            agent_input = block.get("input", {})
            subagent_type = agent_input.get("subagent_type", "")
            prompt = agent_input.get("prompt", "")
            agent_name = _resolve_agent_name(subagent_type, prompt)
            if agent_name:
                model = AGENT_MODELS.get(agent_name, "unknown")
                invocations.append(AgentInvocation(
                    agent_name=agent_name,
                    model=model,
                    round_number=round_number,
                ))
    return invocations


def _resolve_agent_name(subagent_type: str, prompt: str) -> str:
    prompt_lower = prompt.lower()
    if "step-attribution" in subagent_type or "step-attribution" in prompt_lower or "attribution" in prompt_lower:
        return "step-attribution"
    if "variant-reviewer" in subagent_type or "variant-reviewer" in prompt_lower or "reviewer" in prompt_lower:
        return "variant-reviewer"
    if subagent_type:
        return subagent_type
    return ""


def build_manifest(
    log_dir: Path,
    tenant_id: str,
    task_model: str,
    started_at: str,
    completed_at: str,
    duration_seconds: float,
    status: str,
    total_rounds: int,
) -> ExperimentManifest:
    all_invocations: List[AgentInvocation] = []
    for round_file in sorted(log_dir.glob("round-*.json")):
        stem = round_file.stem
        try:
            round_num = int(stem.replace("round-", ""))
        except ValueError:
            continue
        all_invocations.extend(parse_round_file(round_file, round_num))

    return ExperimentManifest(
        tenant_id=tenant_id,
        task_model=task_model,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration_seconds,
        total_rounds=total_rounds,
        agent_invocations=all_invocations,
        agent_summary=summarize_invocations(all_invocations),
        status=status,
    )


def write_manifest(manifest: ExperimentManifest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(manifest)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_manifest(path: Path) -> ExperimentManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    invocations = [
        AgentInvocation(**inv) for inv in data.pop("agent_invocations", [])
    ]
    return ExperimentManifest(agent_invocations=invocations, **data)
