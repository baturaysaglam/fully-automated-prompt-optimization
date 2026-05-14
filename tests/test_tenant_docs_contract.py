# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK_SCRIPT = REPO_ROOT / "scripts" / "check_tenant_docs.py"


def test_tenant_docs_contract_passes_for_existing_tenant():
    tenant_root = REPO_ROOT / "tenants"
    tenant_names = sorted(
        p.name for p in tenant_root.iterdir() if p.is_dir() and not p.name.startswith("_")
    )
    assert tenant_names, "expected at least one tenant directory under tenants/"

    result = subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), "--tenant", tenant_names[0]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "passed" in result.stdout.lower()


def test_tenant_docs_contract_fails_when_required_docs_are_missing(tmp_path: Path):
    tenant_root = tmp_path / "tenants"
    tenant_dir = tenant_root / "demo"
    (tenant_dir / "docs").mkdir(parents=True)
    (tenant_dir / "README.md").write_text("# demo\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCRIPT),
            "--tenant-root",
            str(tenant_root),
            "--tenant",
            "demo",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "missing required file" in result.stderr


def test_tenant_docs_contract_accepts_docs_index_with_four_space_canonical_indent(
    tmp_path: Path,
):
    tenant_root = tmp_path / "tenants"
    tenant_dir = tenant_root / "demo"
    docs_dir = tenant_dir / "docs"
    docs_dir.mkdir(parents=True)

    (tenant_dir / "README.md").write_text("# demo\n", encoding="utf-8")
    (docs_dir / "tenant-profile.md").write_text(
        "\n".join(
            [
                "## Organization Profile",
                "## Security Environment Assumptions",
                "## Threat Model Focus",
                "## Known Safe Patterns",
                "## Tenant Terminology",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (docs_dir / "data-contract.md").write_text(
        "\n".join(
            [
                "## Dataset Inventory",
                "## Case Schema",
                "## Label Taxonomy",
                "## Check Expectations",
                "## Dataset Update Procedure",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (docs_dir / "prompt-contract.md").write_text(
        "\n".join(
            [
                "## Output Format Contract",
                "## Decision Policy",
                "## Defang and Safety Rules",
                "## Variant Strategy",
                "## Non-Goals",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (docs_dir / "eval-operations.md").write_text(
        "\n".join(
            [
                "## Config Matrix",
                "## Standard Eval Commands",
                "## Success Criteria",
                "## Failure Triage",
                "## Output Management",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (docs_dir / "iteration-playbook.md").write_text(
        "\n".join(
            [
                "## Prerequisites",
                "## Iteration Loop",
                "## Stop Criteria",
                "## Regression Prevention",
                "## Lessons Logging",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (docs_dir / "change-log.md").write_text("## 2026-02-10\n", encoding="utf-8")

    (docs_dir / "docs-index.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "tenant_id: demo",
                "canonical_docs:",
                "    tenant_profile: docs/tenant-profile.md",
                "    data_contract: docs/data-contract.md",
                "    prompt_contract: docs/prompt-contract.md",
                "    eval_operations: docs/eval-operations.md",
                "    iteration_playbook: docs/iteration-playbook.md",
                "    change_log: docs/change-log.md",
                "last_validated: 2026-02-10",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCRIPT),
            "--tenant-root",
            str(tenant_root),
            "--tenant",
            "demo",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_tenant_docs_contract_rejects_canonical_doc_path_outside_tenant_root(tmp_path: Path):
    tenant_root = tmp_path / "tenants"
    tenant_dir = tenant_root / "demo"
    docs_dir = tenant_dir / "docs"
    docs_dir.mkdir(parents=True)
    external_doc = tmp_path / "outside.md"
    external_doc.write_text("outside", encoding="utf-8")

    (tenant_dir / "README.md").write_text("# demo\n", encoding="utf-8")
    required_docs = {
        "tenant-profile.md": [
            "## Organization Profile",
            "## Security Environment Assumptions",
            "## Threat Model Focus",
            "## Known Safe Patterns",
            "## Tenant Terminology",
        ],
        "data-contract.md": [
            "## Dataset Inventory",
            "## Case Schema",
            "## Label Taxonomy",
            "## Check Expectations",
            "## Dataset Update Procedure",
        ],
        "prompt-contract.md": [
            "## Output Format Contract",
            "## Decision Policy",
            "## Defang and Safety Rules",
            "## Variant Strategy",
            "## Non-Goals",
        ],
        "eval-operations.md": [
            "## Config Matrix",
            "## Standard Eval Commands",
            "## Success Criteria",
            "## Failure Triage",
            "## Output Management",
        ],
        "iteration-playbook.md": [
            "## Prerequisites",
            "## Iteration Loop",
            "## Stop Criteria",
            "## Regression Prevention",
            "## Lessons Logging",
        ],
    }
    for name, sections in required_docs.items():
        (docs_dir / name).write_text("\n".join(sections) + "\n", encoding="utf-8")
    (docs_dir / "change-log.md").write_text("## 2026-02-10\n", encoding="utf-8")

    (docs_dir / "docs-index.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "tenant_id: demo",
                "canonical_docs:",
                "  tenant_profile: ../outside.md",
                "  data_contract: docs/data-contract.md",
                "  prompt_contract: docs/prompt-contract.md",
                "  eval_operations: docs/eval-operations.md",
                "  iteration_playbook: docs/iteration-playbook.md",
                "  change_log: docs/change-log.md",
                "last_validated: 2026-02-10",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(CHECK_SCRIPT),
            "--tenant-root",
            str(tenant_root),
            "--tenant",
            "demo",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "outside tenant root" in result.stderr
