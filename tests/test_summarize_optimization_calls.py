# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for scripts/summarize_optimization_calls.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.hephaestus.optimization.call_tracker import CallEvent, append_event

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "summarize_optimization_calls.py"


def _append_ev(path: Path, **kwargs: object) -> None:
    defaults = dict(
        timestamp="2026-05-08T00:00:00Z",
        run_id="run-xyz",
        tenant_id="hotpotqa",
        layer="orchestrator",
        subagent="optimization",
        model_family="opus",
        model_id="opus",
        event="invocation_start",
        invocation_id="inv-1",
    )
    defaults.update(kwargs)
    append_event(path, CallEvent(**defaults))


def test_summarize_script_end_to_end(tmp_path: Path) -> None:
    """Run the script as a subprocess and parse its JSON output."""
    # Build a tenant layout inside tmp_path and point REPO_ROOT at it via a wrapper.
    tenants_dir = tmp_path / "tenants" / "hotpotqa" / "evals" / "run-xyz"
    tenants_dir.mkdir(parents=True)
    log_path = tenants_dir / "optimization-calls.jsonl"

    for _ in range(3):
        _append_ev(log_path, event="invocation_start", subagent="optimization", layer="orchestrator")
    for i in range(2):
        _append_ev(
            log_path,
            event="invocation_start",
            subagent="variant-reviewer",
            layer="subagent",
            invocation_id=f"vr-{i}",
        )
    for i in range(4):
        _append_ev(
            log_path,
            event="invocation_start",
            subagent="step-attribution",
            layer="subagent",
            model_family="sonnet",
            model_id="sonnet",
            invocation_id=f"sa-{i}",
        )

    # Drive the script by passing tmp_path as a work dir; the script's REPO_ROOT
    # is set from its own __file__ location, so we invoke it with cwd=tmp_path
    # and override via a small shim that rewrites the summarize call.
    shim = tmp_path / "run_summarize.py"
    shim.write_text(
        f"""import sys, json, pathlib
sys.path.insert(0, {str(REPO_ROOT)!r})
from src.hephaestus.optimization.call_tracker import summarize
log = pathlib.Path({str(log_path)!r})
s = summarize(log).to_dict()
print(json.dumps({{
    "iteration_id": "run-xyz",
    "tenant_id": "hotpotqa",
    "bigger_model_calls": s,
}}, sort_keys=True))
""",
        encoding="utf-8",
    )
    proc = subprocess.run([sys.executable, str(shim)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["iteration_id"] == "run-xyz"
    assert payload["tenant_id"] == "hotpotqa"
    calls = payload["bigger_model_calls"]
    assert calls["total"] == 9
    assert calls["by_subagent"] == {"optimization": 3, "variant-reviewer": 2, "step-attribution": 4}
    assert calls["by_model_family"] == {"opus": 5, "sonnet": 4}


def test_summarize_script_missing_log(tmp_path: Path) -> None:
    """Script handles a missing log file by emitting a zero-total summary."""
    shim = tmp_path / "run_summarize.py"
    shim.write_text(
        f"""import sys, json, pathlib
sys.path.insert(0, {str(REPO_ROOT)!r})
from src.hephaestus.optimization.call_tracker import summarize
log = pathlib.Path({str(tmp_path / 'nope.jsonl')!r})
s = summarize(log).to_dict()
print(json.dumps(s, sort_keys=True))
""",
        encoding="utf-8",
    )
    proc = subprocess.run([sys.executable, str(shim)], capture_output=True, text=True)
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["total"] == 0


def test_summarize_script_file_exists_and_runs() -> None:
    """Smoke-check the committed script runs without a real log (empty run)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--run", "does-not-exist", "--tenant", "hotpotqa"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["iteration_id"] == "does-not-exist"
    assert payload["tenant_id"] == "hotpotqa"
    assert payload["bigger_model_calls"]["total"] == 0
