# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Atomic-append call log + post-hoc summarizer for Claude Code sub-agents.

Design:
  - Each event is written as a single JSON object on its own line.
  - Writes use POSIX ``O_APPEND`` + a single ``os.write`` call; for payloads
    under ``PIPE_BUF`` (typically 4 KB, always > 512 B) this is atomic even
    under concurrent writers.
  - Our events serialize to ~500 bytes; well under PIPE_BUF.
  - The summarizer pairs ``invocation_start`` / ``invocation_end`` events on
    ``invocation_id``, ignoring unmatched events (partial logs from crashes).
"""

from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CallEvent:
    """One sub-agent invocation record.

    Paired ``invocation_start`` + ``invocation_end`` events let us compute
    latency and retain forensic detail even if a run crashes mid-iteration.
    """

    timestamp: str
    run_id: str
    tenant_id: str
    layer: str  # "orchestrator" | "subagent"
    subagent: str  # agent name from .claude/agents/<name>.md
    model_family: str  # "opus" | "sonnet" | "haiku" | explicit id | "unknown"
    model_id: str  # best-effort full model id, or "" if unresolved
    event: str  # "invocation_start" | "invocation_end"
    invocation_id: str
    parent_invocation_id: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    duration_ms: Optional[int] = None


@dataclass
class CallSummary:
    total: int = 0
    by_subagent: Dict[str, int] = field(default_factory=dict)
    by_layer: Dict[str, int] = field(default_factory=dict)
    by_model_family: Dict[str, int] = field(default_factory=dict)
    by_model_id: Dict[str, int] = field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms_total: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "by_subagent": dict(self.by_subagent),
            "by_layer": dict(self.by_layer),
            "by_model_family": dict(self.by_model_family),
            "by_model_id": dict(self.by_model_id),
            "tokens": {"input": self.input_tokens, "output": self.output_tokens},
            "duration_ms_total": self.duration_ms_total,
        }


def append_event(path: Path, event: CallEvent) -> None:
    """Append *event* to *path* as a single JSON line.

    Write is atomic on POSIX for payloads <= PIPE_BUF (always the case for
    our events). Directory is created on demand.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(asdict(event), sort_keys=True).encode("utf-8") + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def _read_events(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    events: List[Dict[str, Any]] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            events.append(json.loads(ln))
        except json.JSONDecodeError:
            # Skip malformed lines rather than crash summarization — forensic
            # logs may be partially truncated.
            continue
    return events


def summarize(path: Path) -> CallSummary:
    """Summarize a call log.

    Counts each ``invocation_start`` event once (so totals are 1:1 with
    invocations, not with event pairs). Token and duration totals sum over
    ``invocation_end`` events, since those are the side of the pair that
    carries usage.
    """
    raw_events = _read_events(path)
    summary = CallSummary()

    by_sub: Counter[str] = Counter()
    by_layer: Counter[str] = Counter()
    by_family: Counter[str] = Counter()
    by_model: Counter[str] = Counter()

    for ev in raw_events:
        if ev.get("event") == "invocation_start":
            summary.total += 1
            by_sub[ev.get("subagent", "")] += 1
            by_layer[ev.get("layer", "")] += 1
            by_family[ev.get("model_family", "")] += 1
            by_model[ev.get("model_id", "")] += 1
        elif ev.get("event") == "invocation_end":
            if isinstance(ev.get("input_tokens"), int):
                summary.input_tokens += ev["input_tokens"]
            if isinstance(ev.get("output_tokens"), int):
                summary.output_tokens += ev["output_tokens"]
            if isinstance(ev.get("duration_ms"), int):
                summary.duration_ms_total += ev["duration_ms"]

    summary.by_subagent = dict(by_sub)
    summary.by_layer = dict(by_layer)
    summary.by_model_family = dict(by_family)
    summary.by_model_id = dict(by_model)
    return summary
