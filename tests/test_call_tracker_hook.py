# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for src/hephaestus/optimization/call_tracker_hook.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.hephaestus.optimization import call_tracker_hook as hook_mod

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clear_frontmatter_cache() -> None:
    hook_mod._agent_frontmatter_cache.clear()
    yield
    hook_mod._agent_frontmatter_cache.clear()


@pytest.fixture()
def redirect_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, Path]:
    """Redirect the hook's filesystem constants to a temp directory.

    Returns (tenants_root, state_dir, agents_dir, unscoped_dir).
    """
    tenants_root = tmp_path / "tenants"
    state_dir = tmp_path / ".claude" / "state"
    agents_dir = tmp_path / ".claude" / "agents"
    unscoped_dir = tenants_root / "_unscoped" / "evals" / "ambient"
    state_dir.mkdir(parents=True)
    agents_dir.mkdir(parents=True)

    monkeypatch.setattr(hook_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(hook_mod, "STATE_DIR", state_dir)
    monkeypatch.setattr(hook_mod, "RUN_ID_FILE", state_dir / "current_run_id")
    monkeypatch.setattr(hook_mod, "TENANT_ID_FILE", state_dir / "current_tenant_id")
    monkeypatch.setattr(hook_mod, "AGENTS_DIR", agents_dir)
    monkeypatch.setattr(hook_mod, "UNSCOPED_LOG_DIR", unscoped_dir)
    monkeypatch.setattr(hook_mod, "HOOK_ERROR_LOG", unscoped_dir / "hook_errors.log")
    return tenants_root, state_dir, agents_dir, unscoped_dir


def _write_agent(agents_dir: Path, name: str, model: str, extra: str = "") -> None:
    (agents_dir / f"{name}.md").write_text(
        f"---\nname: {name}\nmodel: {model}\n{extra}\n---\n# {name} body\n",
        encoding="utf-8",
    )


# --- _read_agent_frontmatter ---


def test_read_agent_frontmatter_extracts_model(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    _, _, agents_dir, _ = redirect_paths
    _write_agent(agents_dir, "optimization", "opus")
    fm = hook_mod._read_agent_frontmatter("optimization")
    assert fm["model"] == "opus"


def test_read_agent_frontmatter_missing_file(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    fm = hook_mod._read_agent_frontmatter("does-not-exist")
    assert fm == {}


# --- _resolve_model ---


def test_resolve_model_opus(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    _, _, agents_dir, _ = redirect_paths
    _write_agent(agents_dir, "optimization", "opus")
    family, model_id = hook_mod._resolve_model("optimization")
    assert family == "opus"
    assert model_id == "opus"


def test_resolve_model_sonnet(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    _, _, agents_dir, _ = redirect_paths
    _write_agent(agents_dir, "step-attribution", "sonnet")
    family, model_id = hook_mod._resolve_model("step-attribution")
    assert family == "sonnet"


def test_resolve_model_haiku(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    _, _, agents_dir, _ = redirect_paths
    _write_agent(agents_dir, "other", "haiku")
    family, _ = hook_mod._resolve_model("other")
    assert family == "haiku"


def test_resolve_model_explicit_id(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    _, _, agents_dir, _ = redirect_paths
    _write_agent(agents_dir, "explicit", "claude-opus-4-7")
    family, model_id = hook_mod._resolve_model("explicit")
    assert family == "opus"
    assert model_id == "claude-opus-4-7"


def test_resolve_model_missing_frontmatter_returns_unknown(
    redirect_paths: tuple[Path, Path, Path, Path],
) -> None:
    family, model_id = hook_mod._resolve_model("nonexistent")
    assert family == "unknown"
    assert model_id == ""


# --- _resolve_output_path + _run ---


def test_run_writes_to_tenant_run_dir(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    tenants_root, state_dir, agents_dir, _ = redirect_paths
    (state_dir / "current_run_id").write_text("run-abc", encoding="utf-8")
    (state_dir / "current_tenant_id").write_text("hotpotqa", encoding="utf-8")
    _write_agent(agents_dir, "optimization", "opus")

    payload = {"agent_type": "optimization", "invocation_id": "inv-1"}
    hook_mod._run("start", payload)

    log = tenants_root / "hotpotqa" / "evals" / "run-abc" / "optimization-calls.jsonl"
    assert log.exists()
    lines = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["event"] == "invocation_start"
    assert parsed["subagent"] == "optimization"
    assert parsed["model_family"] == "opus"
    assert parsed["run_id"] == "run-abc"
    assert parsed["tenant_id"] == "hotpotqa"


def test_run_falls_back_to_ambient_when_state_missing(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    tenants_root, _, agents_dir, _ = redirect_paths
    _write_agent(agents_dir, "optimization", "opus")

    payload = {"agent_type": "optimization", "invocation_id": "inv-1"}
    hook_mod._run("start", payload)

    fallback = tenants_root / "_unscoped" / "evals" / "ambient" / "optimization-calls.jsonl"
    assert fallback.exists()
    lines = [ln for ln in fallback.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1


def test_run_dynamic_frontmatter_resolution(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    """If an unknown agent is spawned with model: haiku in its frontmatter,
    the tracker tags events with ``model_family: haiku``."""
    tenants_root, state_dir, agents_dir, _ = redirect_paths
    (state_dir / "current_run_id").write_text("run-abc", encoding="utf-8")
    (state_dir / "current_tenant_id").write_text("hotpotqa", encoding="utf-8")
    _write_agent(agents_dir, "xyz", "haiku")

    hook_mod._run("start", {"agent_type": "xyz", "invocation_id": "inv-1"})

    log = tenants_root / "hotpotqa" / "evals" / "run-abc" / "optimization-calls.jsonl"
    lines = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
    parsed = json.loads(lines[0])
    assert parsed["model_family"] == "haiku"


def test_run_captures_tokens_and_duration(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    tenants_root, state_dir, agents_dir, _ = redirect_paths
    (state_dir / "current_run_id").write_text("run-abc", encoding="utf-8")
    (state_dir / "current_tenant_id").write_text("hotpotqa", encoding="utf-8")
    _write_agent(agents_dir, "optimization", "opus")

    payload = {
        "agent_type": "optimization",
        "invocation_id": "inv-1",
        "input_tokens": 1000,
        "output_tokens": 200,
        "duration_ms": 500,
    }
    hook_mod._run("end", payload)

    log = tenants_root / "hotpotqa" / "evals" / "run-abc" / "optimization-calls.jsonl"
    parsed = json.loads(log.read_text().splitlines()[0])
    assert parsed["event"] == "invocation_end"
    assert parsed["input_tokens"] == 1000
    assert parsed["output_tokens"] == 200
    assert parsed["duration_ms"] == 500


# --- error swallow ---


def test_malformed_stdin_does_not_raise(
    redirect_paths: tuple[Path, Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hook must never raise to avoid blocking /optimization."""
    import io

    fake_stdin = io.StringIO("NOT VALID JSON")
    fake_stdin.isatty = lambda: False  # type: ignore[method-assign]
    monkeypatch.setattr(sys, "stdin", fake_stdin)
    sys.argv[:] = ["call_tracker_hook", "start"]
    rc = hook_mod.main()
    assert rc == 0
    # Sentinel error log should contain an entry.
    _, _, _, unscoped_dir = redirect_paths
    err_log = unscoped_dir / "hook_errors.log"
    assert err_log.exists()
    assert "ValueError" in err_log.read_text()


def test_self_test_writes_an_event(redirect_paths: tuple[Path, Path, Path, Path]) -> None:
    """The --self-test flag appends one synthetic event."""
    tenants_root, state_dir, agents_dir, _ = redirect_paths
    (state_dir / "current_run_id").write_text("selftest-run", encoding="utf-8")
    (state_dir / "current_tenant_id").write_text("hotpotqa", encoding="utf-8")
    _write_agent(agents_dir, "optimization", "opus")

    sys.argv[:] = ["call_tracker_hook", "--self-test"]
    rc = hook_mod.main()
    assert rc == 0
    log = tenants_root / "hotpotqa" / "evals" / "selftest-run" / "optimization-calls.jsonl"
    assert log.exists()
    assert log.read_text().count("\n") == 1


# --- subprocess end-to-end ---


def test_subprocess_stdin_writes_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the hook as the real Claude Code would: as a subprocess with JSON on stdin."""
    # Set up a sandbox copy of the hook filesystem.
    state_dir = tmp_path / ".claude" / "state"
    agents_dir = tmp_path / ".claude" / "agents"
    state_dir.mkdir(parents=True)
    agents_dir.mkdir(parents=True)
    (state_dir / "current_run_id").write_text("sub-run", encoding="utf-8")
    (state_dir / "current_tenant_id").write_text("hotpotqa", encoding="utf-8")
    (agents_dir / "optimization.md").write_text(
        "---\nname: optimization\nmodel: opus\n---\n# body\n", encoding="utf-8"
    )

    script = tmp_path / "run_hook.py"
    script.write_text(
        f"""import sys, runpy
# Point the hook's REPO_ROOT at our sandbox by monkey-patching before import.
import importlib.util
sys.path.insert(0, {str(REPO_ROOT)!r})
from src.hephaestus.optimization import call_tracker_hook as m
m.REPO_ROOT = __import__('pathlib').Path({str(tmp_path)!r})
m.STATE_DIR = m.REPO_ROOT / '.claude' / 'state'
m.RUN_ID_FILE = m.STATE_DIR / 'current_run_id'
m.TENANT_ID_FILE = m.STATE_DIR / 'current_tenant_id'
m.AGENTS_DIR = m.REPO_ROOT / '.claude' / 'agents'
m.UNSCOPED_LOG_DIR = m.REPO_ROOT / 'tenants' / '_unscoped' / 'evals' / 'ambient'
m.HOOK_ERROR_LOG = m.UNSCOPED_LOG_DIR / 'hook_errors.log'
sys.argv[:] = ['hook', sys.argv[1]]
sys.exit(m.main())
""",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, str(script), "start"],
        input=json.dumps({"agent_type": "optimization", "invocation_id": "sub-inv"}),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    log = tmp_path / "tenants" / "hotpotqa" / "evals" / "sub-run" / "optimization-calls.jsonl"
    assert log.exists(), f"log missing; stderr={proc.stderr}"
    parsed = json.loads(log.read_text().splitlines()[0])
    assert parsed["subagent"] == "optimization"
    assert parsed["model_family"] == "opus"
