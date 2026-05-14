# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for run-fepo.sh and monitor-fepo.sh experiment scripts."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent.parent
RUN_SCRIPT = EXPERIMENTS_DIR / "run-fepo.sh"
MONITOR_SCRIPT = EXPERIMENTS_DIR / "monitor-fepo.sh"


def _run_script(
    script: Path,
    env_override: dict | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    env = env_override if env_override is not None else os.environ.copy()
    return subprocess.run(
        ["/bin/bash", str(script)],
        capture_output=True, text=True, env=env,
        cwd=str(cwd or EXPERIMENTS_DIR),
        timeout=10,
    )


def _make_mock_bin(tmp_path: Path, sessions: list[str] | None = None, conda_exists: bool = True) -> Path:
    """Create mock tmux and conda scripts. Returns the mock bin directory."""
    mock_bin = tmp_path / "mockbin"
    mock_bin.mkdir(exist_ok=True)

    session_list = sessions or []

    # Mock tmux
    tmux_script = mock_bin / "tmux"
    tmux_script.write_text(f"""\
#!/bin/bash
SESSIONS=({' '.join(f'"{s}"' for s in session_list)})

if [[ "$1" == "has-session" ]]; then
    target="${{3:-}}"
    for s in "${{SESSIONS[@]}}"; do
        if [[ "$s" == "$target" ]]; then exit 0; fi
    done
    exit 1
elif [[ "$1" == "new-session" ]]; then
    echo "TMUX_NEW_SESSION: $*" >> "{tmp_path}/tmux_calls.log"
    exit 0
elif [[ "$1" == "list-sessions" ]]; then
    for s in "${{SESSIONS[@]}}"; do
        echo "$s: 1 windows"
    done
    exit 0
fi
exit 0
""", encoding="utf-8")
    tmux_script.chmod(tmux_script.stat().st_mode | stat.S_IEXEC)

    # Mock conda
    conda_script = mock_bin / "conda"
    if conda_exists:
        conda_script.write_text("""\
#!/bin/bash
if [[ "$1" == "env" && "$2" == "list" ]]; then
    echo "fepo                     /mock/envs/fepo"
    exit 0
fi
exit 0
""", encoding="utf-8")
    else:
        conda_script.write_text("""\
#!/bin/bash
if [[ "$1" == "env" && "$2" == "list" ]]; then
    echo "base                     /mock/envs/base"
    exit 0
fi
exit 0
""", encoding="utf-8")
    conda_script.chmod(conda_script.stat().st_mode | stat.S_IEXEC)

    return mock_bin


def _build_env(mock_bin: Path, include_key: bool = True, results_dir: Path | None = None) -> dict:
    """Build a test environment with mock bin prepended to PATH."""
    env = {
        "PATH": f"{mock_bin}:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": os.environ.get("HOME", "/tmp"),
    }
    if include_key:
        env["OPENAI_API_KEY"] = "test-key-for-testing"
    if results_dir is not None:
        env["FEPO_RESULTS_DIR"] = str(results_dir)
    return env


# =============================================================================
# run-fepo.sh Tests
# =============================================================================


class TestRunFepoPreflight:
    """Preflight checks in run-fepo.sh."""

    def test_missing_tmux(self, tmp_path: Path):
        """Exits with error if tmux is not on PATH."""
        mock_bin = tmp_path / "mockbin"
        mock_bin.mkdir()
        # Only conda, no tmux
        conda_script = mock_bin / "conda"
        conda_script.write_text("#!/bin/bash\necho 'fepo /e/fepo'; exit 0\n", encoding="utf-8")
        conda_script.chmod(conda_script.stat().st_mode | stat.S_IEXEC)

        env = {"PATH": f"{mock_bin}:/usr/bin:/bin", "HOME": "/tmp", "OPENAI_API_KEY": "x"}
        result = _run_script(RUN_SCRIPT, env_override=env)
        assert result.returncode != 0
        assert "tmux" in result.stderr.lower()

    def test_missing_conda_env(self, tmp_path: Path):
        """Exits with error if fepo conda env doesn't exist."""
        mock_bin = _make_mock_bin(tmp_path, conda_exists=False)
        env = _build_env(mock_bin)
        result = _run_script(RUN_SCRIPT, env_override=env)
        assert result.returncode != 0
        assert "fepo" in result.stderr

    def test_missing_openai_key(self, tmp_path: Path):
        """Exits with error if OPENAI_API_KEY is not set."""
        mock_bin = _make_mock_bin(tmp_path)
        env = _build_env(mock_bin, include_key=False)
        result = _run_script(RUN_SCRIPT, env_override=env)
        assert result.returncode != 0
        assert "OPENAI_API_KEY" in result.stderr


class TestRunFepoLaunch:
    """Session launch behavior."""

    def test_creates_sessions_for_all_datasets(self, tmp_path: Path):
        """Creates one tmux session per dataset."""
        mock_bin = _make_mock_bin(tmp_path, sessions=[])
        env = _build_env(mock_bin)
        result = _run_script(RUN_SCRIPT, env_override=env)
        assert result.returncode == 0

        log_file = tmp_path / "tmux_calls.log"
        assert log_file.exists(), f"No tmux calls logged. stdout={result.stdout} stderr={result.stderr}"
        calls = log_file.read_text(encoding="utf-8")

        expected_sessions = ["fepo-hotpotqa", "fepo-ifbench", "fepo-hover",
                            "fepo-pupa", "fepo-aime2025", "fepo-livebench-math"]
        for sess in expected_sessions:
            assert sess in calls, f"Session {sess} not created"

    def test_skips_existing_sessions(self, tmp_path: Path):
        """Does not recreate sessions that already exist."""
        mock_bin = _make_mock_bin(tmp_path, sessions=["fepo-hotpotqa", "fepo-hover"])
        env = _build_env(mock_bin)
        result = _run_script(RUN_SCRIPT, env_override=env)
        assert result.returncode == 0
        assert "already exists" in result.stdout

        log_file = tmp_path / "tmux_calls.log"
        calls = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
        assert "fepo-hotpotqa" not in calls
        assert "fepo-hover" not in calls
        assert "fepo-ifbench" in calls

    def test_task_model_in_session_command(self, tmp_path: Path):
        """--task-model is passed to optimize-loop.sh."""
        mock_bin = _make_mock_bin(tmp_path, sessions=[])
        env = _build_env(mock_bin)
        _run_script(RUN_SCRIPT, env_override=env)

        log_file = tmp_path / "tmux_calls.log"
        calls = log_file.read_text(encoding="utf-8")
        assert "--task-model" in calls
        assert "gpt-4.1-mini" in calls

    def test_goal_passed_for_each_dataset(self, tmp_path: Path):
        """Each session gets its dataset-specific goal."""
        mock_bin = _make_mock_bin(tmp_path, sessions=[])
        env = _build_env(mock_bin)
        _run_script(RUN_SCRIPT, env_override=env)

        log_file = tmp_path / "tmux_calls.log"
        calls = log_file.read_text(encoding="utf-8")
        assert "--goal" in calls
        assert "--tenant" in calls


# =============================================================================
# monitor-fepo.sh Tests
# =============================================================================


class TestMonitorFepo:
    """Tests for monitor-fepo.sh output."""

    def test_no_runs_shows_not_started(self, tmp_path: Path):
        """With no optimize-loop output, all datasets show NOT STARTED."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        mock_bin = _make_mock_bin(tmp_path, sessions=[])
        env = _build_env(mock_bin, results_dir=results_dir)
        result = _run_script(MONITOR_SCRIPT, env_override=env)
        assert result.returncode == 0
        assert "NOT STARTED" in result.stdout

    def test_running_session_detected(self, tmp_path: Path):
        """Active tmux sessions show as RUNNING."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        mock_bin = _make_mock_bin(tmp_path, sessions=["fepo-hotpotqa"])
        env = _build_env(mock_bin, results_dir=results_dir)
        result = _run_script(MONITOR_SCRIPT, env_override=env)
        assert result.returncode == 0
        assert "RUNNING" in result.stdout

    def test_progress_log_parsing(self, tmp_path: Path):
        """Correctly extracts round number from progress.log."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        test_dir = results_dir / "hotpotqa-20260512-100000"
        test_dir.mkdir()

        progress_log = test_dir / "progress.log"
        progress_log.write_text(
            '2026-05-12T10:00:00+00:00 round=1 status="requirements not met"\n'
            '2026-05-12T10:15:00+00:00 round=2 status="requirements not met"\n'
            '2026-05-12T10:30:00+00:00 round=3 status="requirements met"\n',
            encoding="utf-8",
        )

        mock_bin = _make_mock_bin(tmp_path, sessions=[])
        env = _build_env(mock_bin, results_dir=results_dir)
        result = _run_script(MONITOR_SCRIPT, env_override=env)
        assert result.returncode == 0
        assert "3" in result.stdout
        assert "STOPPED" in result.stdout

    def test_manifest_shows_completed(self, tmp_path: Path):
        """Shows COMPLETED and agent call counts from experiment-manifest.json."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        test_dir = results_dir / "ifbench-20260512-110000"
        test_dir.mkdir()

        progress_log = test_dir / "progress.log"
        progress_log.write_text(
            '2026-05-12T11:00:00+00:00 round=1 status="requirements met"\n',
            encoding="utf-8",
        )
        manifest = test_dir / "experiment-manifest.json"
        manifest.write_text(json.dumps({
            "tenant_id": "ifbench",
            "task_model": "gpt-4.1-mini",
            "started_at": "2026-05-12T11:00:00+00:00",
            "completed_at": "2026-05-12T11:20:00+00:00",
            "duration_seconds": 1200.0,
            "total_rounds": 1,
            "agent_invocations": [],
            "agent_summary": {
                "total_agent_calls": 5,
                "by_agent": {"optimization": 1, "step-attribution": 2, "variant-reviewer": 2},
                "by_model": {"opus": 3, "sonnet": 2},
            },
            "status": "success",
        }), encoding="utf-8")

        mock_bin = _make_mock_bin(tmp_path, sessions=[])
        env = _build_env(mock_bin, results_dir=results_dir)
        result = _run_script(MONITOR_SCRIPT, env_override=env)
        assert result.returncode == 0
        assert "COMPLETED" in result.stdout
        assert "5 calls" in result.stdout

    def test_active_session_count(self, tmp_path: Path):
        """Footer shows correct active session count."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        mock_bin = _make_mock_bin(tmp_path, sessions=["fepo-hotpotqa", "fepo-pupa"])
        env = _build_env(mock_bin, results_dir=results_dir)
        result = _run_script(MONITOR_SCRIPT, env_override=env)
        assert result.returncode == 0
        assert "Active sessions: 2 / 6" in result.stdout


# =============================================================================
# Syntax validation
# =============================================================================


class TestScriptSyntax:
    """Basic validity checks."""

    def test_run_fepo_syntax(self):
        """run-fepo.sh has valid bash syntax."""
        result = subprocess.run(["/bin/bash", "-n", str(RUN_SCRIPT)], capture_output=True, text=True)
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_monitor_fepo_syntax(self):
        """monitor-fepo.sh has valid bash syntax."""
        result = subprocess.run(["/bin/bash", "-n", str(MONITOR_SCRIPT)], capture_output=True, text=True)
        assert result.returncode == 0, f"Syntax error: {result.stderr}"
