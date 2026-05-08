# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Hook entry point invoked by Claude Code's SubagentStart/SubagentStop events.

Claude Code sends hook payloads on stdin as JSON. We read the payload, resolve
the acting subagent's model family from its ``.claude/agents/<name>.md``
frontmatter, and append a ``CallEvent`` to an optimization-run JSONL file.

Output path convention:
  ``tenants/<tenant_id>/evals/<run_id>/optimization-calls.jsonl``

The ``run_id`` is resolved from ``.claude/state/current_run_id``; the
``tenant_id`` from ``.claude/state/current_tenant_id``. Files, not env vars,
because env-var propagation across Claude Code subagent boundaries is not
reliable. When either file is missing, fall back to
``tenants/_unscoped/evals/ambient/``.

Robustness:
  Any exception raised inside the hook is caught, logged to a sentinel file,
  and swallowed — the hook script must never block ``/optimization``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from .call_tracker import CallEvent, append_event

REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_DIR = REPO_ROOT / ".claude" / "state"
RUN_ID_FILE = STATE_DIR / "current_run_id"
TENANT_ID_FILE = STATE_DIR / "current_tenant_id"
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
UNSCOPED_LOG_DIR = REPO_ROOT / "tenants" / "_unscoped" / "evals" / "ambient"
HOOK_ERROR_LOG = UNSCOPED_LOG_DIR / "hook_errors.log"

# Known Claude Code model-family aliases per ``docs.claude.com/docs/en/model-config.md``.
# If the frontmatter ``model:`` value matches one of these, we tag events with
# the canonical family; any other value is passed through verbatim.
_MODEL_FAMILIES = {"opus", "sonnet", "haiku"}


# Small per-process cache: parsing the same agent markdown repeatedly would
# waste I/O when the hook fires many times in one session.
_agent_frontmatter_cache: Dict[str, Dict[str, str]] = {}


def _read_state(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _read_agent_frontmatter(agent_name: str) -> Dict[str, str]:
    """Parse the YAML-style frontmatter block in ``.claude/agents/<agent>.md``.

    Returns a dict of string keys to stripped string values. Unknown fields
    are preserved. Missing / unparseable → empty dict.
    """
    if agent_name in _agent_frontmatter_cache:
        return _agent_frontmatter_cache[agent_name]

    result: Dict[str, str] = {}
    path = AGENTS_DIR / f"{agent_name}.md"
    if not path.exists():
        _agent_frontmatter_cache[agent_name] = result
        return result
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        _agent_frontmatter_cache[agent_name] = result
        return result

    # Frontmatter is delimited by lines starting with '---'. We accept an
    # optional preamble (e.g., a copyright comment block) before the first '---'.
    matches = re.findall(r"(?m)^---\s*$", text)
    if len(matches) < 2:
        _agent_frontmatter_cache[agent_name] = result
        return result
    first_idx = text.index("---")
    second_idx = text.index("---", first_idx + 3)
    block = text[first_idx + 3 : second_idx]

    # Very simple key: value parser. Values may span multiple lines using
    # YAML's ``>`` block folding; we flatten them into a single string.
    current_key: Optional[str] = None
    current_val: list[str] = []
    for raw_line in block.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        m = re.match(r"^(\w[\w_]*)\s*:\s*(.*)$", line)
        if m and not line.startswith(" "):
            if current_key is not None:
                result[current_key] = " ".join(current_val).strip().strip(">").strip()
            current_key = m.group(1)
            current_val = [m.group(2)]
        else:
            current_val.append(line.strip())
    if current_key is not None:
        result[current_key] = " ".join(current_val).strip().strip(">").strip()

    _agent_frontmatter_cache[agent_name] = result
    return result


def _resolve_model(agent_name: str) -> tuple[str, str]:
    """Return ``(model_family, model_id)`` for a subagent.

    Resolution order:
      1. Read the agent's frontmatter ``model:`` field.
      2. If the value is one of {opus, sonnet, haiku} → that's the family;
         model_id is the same string (the canonical alias Claude Code resolves).
      3. If the value looks like an explicit id (e.g. ``claude-opus-4-7``),
         split on ``-`` to recover the family.
      4. Missing / unparseable → ("unknown", "").
    """
    fm = _read_agent_frontmatter(agent_name)
    raw = (fm.get("model") or "").strip()
    if not raw:
        return ("unknown", "")
    if raw in _MODEL_FAMILIES:
        return (raw, raw)
    # Explicit ids look like ``claude-<family>-<rest>``; fall back to unknown.
    parts = raw.split("-")
    if len(parts) >= 2 and parts[0] == "claude":
        family = parts[1]
        return (family if family in _MODEL_FAMILIES else family, raw)
    return ("unknown", raw)


def _resolve_output_path() -> Path:
    run_id = _read_state(RUN_ID_FILE) or "ambient"
    tenant_id = _read_state(TENANT_ID_FILE) or "_unscoped"
    return REPO_ROOT / "tenants" / tenant_id / "evals" / run_id / "optimization-calls.jsonl"


def _build_event(event_name: str, payload: Dict[str, Any]) -> CallEvent:
    # Claude Code payload fields that may be present (verified against
    # docs.claude.com/docs/en/hooks.md; ``SubagentStart``/``SubagentStop``
    # payloads include session_id and subagent identifier but the exact
    # field keys are not fully documented. We accept several common shapes).
    subagent = (
        payload.get("agent_type")
        or payload.get("subagent_type")
        or payload.get("subagent")
        or payload.get("agent")
        or ""
    )
    subagent = str(subagent).strip()
    invocation_id = (
        payload.get("invocation_id")
        or payload.get("agent_session_id")
        or payload.get("subagent_session_id")
        or payload.get("session_id")
        or str(uuid.uuid4())
    )
    parent_invocation_id = (
        payload.get("parent_invocation_id")
        or payload.get("parent_session_id")
        or None
    )
    input_tokens = payload.get("input_tokens")
    output_tokens = payload.get("output_tokens")
    duration_ms = payload.get("duration_ms")
    model_family, model_id = _resolve_model(subagent) if subagent else ("unknown", "")

    # Heuristic: SubagentStart for the top-level ``optimization`` agent has no
    # parent; nested subagents (variant-reviewer, step-attribution) do. Layer
    # tag is informational only and is safe to be wrong.
    layer = "orchestrator" if subagent == "optimization" and not parent_invocation_id else "subagent"

    return CallEvent(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int((time.time()%1)*1000):03d}Z",
        run_id=_read_state(RUN_ID_FILE) or "ambient",
        tenant_id=_read_state(TENANT_ID_FILE) or "_unscoped",
        layer=layer,
        subagent=subagent,
        model_family=model_family,
        model_id=model_id,
        event=event_name,
        invocation_id=str(invocation_id),
        parent_invocation_id=str(parent_invocation_id) if parent_invocation_id else None,
        input_tokens=input_tokens if isinstance(input_tokens, int) else None,
        output_tokens=output_tokens if isinstance(output_tokens, int) else None,
        duration_ms=duration_ms if isinstance(duration_ms, int) else None,
    )


def _log_hook_error(exc: BaseException) -> None:
    """Write a single line to the diagnostic sentinel; never raises."""
    try:
        UNSCOPED_LOG_DIR.mkdir(parents=True, exist_ok=True)
        line = (
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            + f" {type(exc).__name__}: {exc!s}\n"
            + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            + "\n"
        )
        with HOOK_ERROR_LOG.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:  # noqa: BLE001
        pass


def _run(event_kind: str, payload: Dict[str, Any]) -> None:
    event_name = "invocation_start" if event_kind == "start" else "invocation_end"
    event = _build_event(event_name, payload)
    append_event(_resolve_output_path(), event)


def _read_payload_from_stdin() -> Dict[str, Any]:
    # Claude Code sends JSON on stdin. If stdin is empty (direct invocation or
    # misconfigured hook), return an empty dict and rely on defaults.
    if sys.stdin.isatty():
        return {}
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Hook received non-JSON stdin: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Hook stdin JSON must be an object, got {type(data).__name__}")
    return data


def _self_test() -> int:
    """Round-trip a synthetic payload through the full pipeline.

    Exits 0 on success, 1 on failure. Used for wiring validation without
    needing to spawn a real Claude Code session.
    """
    synthetic = {
        "hook_event_name": "SubagentStart",
        "session_id": "selftest-session",
        "agent_type": "optimization",
        "invocation_id": "selftest-inv",
    }
    output_path = _resolve_output_path()
    before = output_path.stat().st_size if output_path.exists() else 0
    event = _build_event("invocation_start", synthetic)
    append_event(output_path, event)
    after = output_path.stat().st_size
    if after <= before:
        print("self-test FAILED: no bytes written", file=sys.stderr)
        return 1
    print(f"self-test ok: appended 1 event to {output_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Claude Code SubagentStart/Stop hook for FEPO.")
    parser.add_argument("event", choices=["start", "end", "--self-test"], nargs="?", default=None)
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    args = parser.parse_args()

    if args.self_test or args.event == "--self-test":
        return _self_test()
    if args.event not in ("start", "end"):
        print("usage: call_tracker_hook {start|end}", file=sys.stderr)
        return 0  # Never non-zero: the hook must not block /optimization.

    try:
        payload = _read_payload_from_stdin()
        _run(args.event, payload)
    except BaseException as exc:  # noqa: BLE001
        _log_hook_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
