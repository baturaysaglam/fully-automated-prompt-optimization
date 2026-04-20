# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
from pathlib import Path


def test_customer_artifact_payloads_are_not_git_tracked():
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    tracked = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    allowed_suffixes = {
        "source_artifacts/.gitkeep",
        "datasets/.gitkeep",
    }

    violations = []
    for path in tracked:
        if (
            path.startswith("tenants/")
            and "/source_artifacts/" in f"/{path}"
            and not any(path.endswith(s) for s in allowed_suffixes)
        ):
            violations.append(path)
        if (
            path.startswith("tenants/")
            and "/datasets/" in f"/{path}"
            and not any(path.endswith(s) for s in allowed_suffixes)
        ):
            violations.append(path)

    assert not violations, f"Tracked customer artifact payload files found: {violations}"
