# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""
Verification tests for experiment configuration invariants:
- Temperature=1.0 across all tenant configs (immutable experimental constant)
- Model name NOT hardcoded in enforcement docs (determined by baseline config)
- Threshold values correctly set in playbooks
"""

import glob
import json
import os
import re
import subprocess

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXPERIMENTAL_TENANTS = [
    "aime2025",
    "cti_rcm",
    "hotpotqa",
    "hover",
    "ifbench",
    "livebench_math",
    "papillon",
]

ENFORCEMENT_DOC_PATHS = [
    "docs/processes/prompt-iteration-loop.md",
    ".claude/agents/optimization.md",
    ".claude/agents/variant-reviewer.md",
] + [f"tenants/{t}/docs/iteration-playbook.md" for t in EXPERIMENTAL_TENANTS]

MODEL_NAME_RE = re.compile(
    r"\bgpt-[34][^\s,)]*|\bclaude-[^\s,)]*|\bgemini-[^\s,)]*|\bllama-[^\s,)]*",
    re.IGNORECASE,
)


def _rel(path):
    return os.path.join(PROJECT_ROOT, path)


def _extract_section(content: str, heading: str) -> str:
    """Extract markdown section text from ## heading to next ## or EOF."""
    pattern = rf"^## {re.escape(heading)}.*?\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def _load_all_eval_configs():
    """Load all tenant eval config JSON files."""
    configs = glob.glob(_rel("tenants/*/configs/*.json"))
    return [(path, json.load(open(path))) for path in configs]


# ---------------------------------------------------------------------------
# Group 1: Config Value Tests
# ---------------------------------------------------------------------------


class TestConfigValues:

    def test_all_configs_temperature_one(self):
        """Every provider_settings.temperature must be 1.0."""
        configs = glob.glob(_rel("tenants/*/configs/*.json"))
        assert len(configs) > 0, "No config files found"
        for path in configs:
            with open(path) as f:
                config = json.load(f)
            if "provider_settings" in config:
                temp = config["provider_settings"].get("temperature")
                assert temp == 1.0, (
                    f"{os.path.relpath(path, PROJECT_ROOT)}: "
                    f"temperature is {temp}, expected 1.0"
                )

    def test_all_configs_top_p(self):
        """Every provider_settings.top_p must be 0.95."""
        configs = glob.glob(_rel("tenants/*/configs/*.json"))
        assert len(configs) > 0, "No config files found"
        for path in configs:
            with open(path) as f:
                config = json.load(f)
            if "provider_settings" in config:
                top_p = config["provider_settings"].get("top_p")
                assert top_p == 0.95, (
                    f"{os.path.relpath(path, PROJECT_ROOT)}: "
                    f"top_p is {top_p}, expected 0.95"
                )

    def test_all_configs_max_tokens(self):
        """Every provider_settings.max_tokens must be 16000."""
        configs = glob.glob(_rel("tenants/*/configs/*.json"))
        assert len(configs) > 0, "No config files found"
        for path in configs:
            with open(path) as f:
                config = json.load(f)
            if "provider_settings" in config:
                max_tokens = config["provider_settings"].get("max_tokens")
                assert max_tokens == 16000, (
                    f"{os.path.relpath(path, PROJECT_ROOT)}: "
                    f"max_tokens is {max_tokens}, expected 16000"
                )

    def test_papillon_untrusted_model_temperature(self):
        """Papillon untrusted_model.temperature must be 1.0."""
        configs = glob.glob(_rel("tenants/papillon/configs/*.json"))
        assert len(configs) > 0, "No papillon config files found"
        for path in configs:
            with open(path) as f:
                config = json.load(f)
            chain_config = config.get("chain", {}).get("config", {})
            if "untrusted_model" in chain_config:
                temp = chain_config["untrusted_model"].get("temperature")
                assert temp == 1.0, (
                    f"{os.path.relpath(path, PROJECT_ROOT)}: "
                    f"untrusted_model temperature is {temp}, must be 1.0"
                )

    @pytest.mark.parametrize("tenant", EXPERIMENTAL_TENANTS)
    def test_model_consistent_within_tenant(self, tenant):
        """All configs for a single tenant must use the same model."""
        configs = glob.glob(_rel(f"tenants/{tenant}/configs/*.json"))
        if not configs:
            pytest.skip(f"No eval configs for {tenant}")
        models = set()
        for path in configs:
            with open(path) as f:
                config = json.load(f)
            if "provider_settings" in config:
                model = config["provider_settings"].get("model")
                if model:
                    models.add(model)
        assert len(models) <= 1, (
            f"{tenant}: found multiple models across configs: {models}"
        )


# ---------------------------------------------------------------------------
# Group 2: Enforcement Doc Tests
# ---------------------------------------------------------------------------


class TestEnforcementDocs:

    def test_global_doc_declares_temperature(self):
        """prompt-iteration-loop.md Experimental Constants must declare temperature=1.0."""
        path = _rel("docs/processes/prompt-iteration-loop.md")
        content = open(path).read()
        section = _extract_section(content, "Experimental Constants")
        assert section, "Missing '## Experimental Constants' section"
        assert "temperature" in section.lower()
        assert "1.0" in section

    def test_global_doc_model_from_baseline(self):
        """prompt-iteration-loop.md must say model is set per-experiment/baseline config."""
        path = _rel("docs/processes/prompt-iteration-loop.md")
        content = open(path).read()
        section = _extract_section(content, "Experimental Constants")
        assert "baseline config" in section.lower() or "per-experiment" in section.lower(), (
            "Experimental Constants section must reference baseline config for model"
        )

    def test_global_doc_no_hardcoded_model(self):
        """prompt-iteration-loop.md Experimental Constants must not hardcode a model name."""
        path = _rel("docs/processes/prompt-iteration-loop.md")
        content = open(path).read()
        section = _extract_section(content, "Experimental Constants")
        matches = MODEL_NAME_RE.findall(section)
        assert not matches, (
            f"Experimental Constants section hardcodes model name(s): {matches}"
        )

    @pytest.mark.parametrize("tenant", EXPERIMENTAL_TENANTS)
    def test_playbook_has_fixed_params_section(self, tenant):
        """Each tenant playbook must have a Fixed Experimental Parameters section."""
        path = _rel(f"tenants/{tenant}/docs/iteration-playbook.md")
        content = open(path).read()
        assert "## Fixed Experimental Parameters" in content, (
            f"{tenant} playbook missing '## Fixed Experimental Parameters' section"
        )

    @pytest.mark.parametrize("tenant", EXPERIMENTAL_TENANTS)
    def test_playbook_declares_temperature(self, tenant):
        """Each playbook Fixed Experimental Parameters must list temperature: 1.0."""
        path = _rel(f"tenants/{tenant}/docs/iteration-playbook.md")
        content = open(path).read()
        section = _extract_section(content, "Fixed Experimental Parameters")
        assert "`temperature`: 1.0" in section, (
            f"{tenant} playbook missing temperature: 1.0 in Fixed Experimental Parameters"
        )

    @pytest.mark.parametrize("tenant", EXPERIMENTAL_TENANTS)
    def test_playbook_declares_top_p(self, tenant):
        """Each playbook Fixed Experimental Parameters must list top_p: 0.95."""
        path = _rel(f"tenants/{tenant}/docs/iteration-playbook.md")
        content = open(path).read()
        section = _extract_section(content, "Fixed Experimental Parameters")
        assert "`top_p`: 0.95" in section, (
            f"{tenant} playbook missing top_p: 0.95 in Fixed Experimental Parameters"
        )

    @pytest.mark.parametrize("tenant", EXPERIMENTAL_TENANTS)
    def test_playbook_declares_max_tokens(self, tenant):
        """Each playbook Fixed Experimental Parameters must list max_tokens: 16000."""
        path = _rel(f"tenants/{tenant}/docs/iteration-playbook.md")
        content = open(path).read()
        section = _extract_section(content, "Fixed Experimental Parameters")
        assert "`max_tokens`: 16000" in section, (
            f"{tenant} playbook missing max_tokens: 16000 in Fixed Experimental Parameters"
        )

    @pytest.mark.parametrize("tenant", EXPERIMENTAL_TENANTS)
    def test_playbook_no_hardcoded_model(self, tenant):
        """Each playbook must not hardcode a model name in Fixed Experimental Parameters."""
        path = _rel(f"tenants/{tenant}/docs/iteration-playbook.md")
        content = open(path).read()
        section = _extract_section(content, "Fixed Experimental Parameters")
        matches = MODEL_NAME_RE.findall(section)
        assert not matches, (
            f"{tenant} playbook hardcodes model name(s) in Fixed Experimental "
            f"Parameters: {matches}"
        )
        assert "baseline config" in section.lower(), (
            f"{tenant} playbook must reference 'baseline config' for model"
        )

    def test_optimization_agent_temperature_immutable(self):
        """optimization.md must list temperature as an immutable parameter."""
        path = _rel(".claude/agents/optimization.md")
        content = open(path).read()
        immutable_line = ""
        for line in content.splitlines():
            if "**Immutable parameters**" in line or "**Immutable experimental parameters**" in line:
                immutable_line += line
        assert "temperature" in immutable_line, (
            "optimization.md does not list temperature as immutable"
        )

    def test_optimization_agent_temperature_not_in_knobs(self):
        """optimization.md must NOT list temperature in Common parameter knobs."""
        path = _rel(".claude/agents/optimization.md")
        content = open(path).read()
        for line in content.splitlines():
            if "Common parameter knobs" in line:
                assert "temperature" not in line, (
                    "optimization.md still lists temperature as a common parameter knob"
                )
                break
        else:
            pytest.fail("optimization.md missing 'Common parameter knobs' line")

    def test_variant_reviewer_has_immutability_check(self):
        """variant-reviewer.md must have Parameter Immutability check mentioning temperature."""
        path = _rel(".claude/agents/variant-reviewer.md")
        content = open(path).read()
        assert "Parameter Immutability" in content, (
            "variant-reviewer.md missing 'Parameter Immutability' check"
        )
        section_start = content.find("Parameter Immutability")
        section_text = content[section_start:section_start + 500]
        assert "temperature" in section_text, (
            "variant-reviewer.md Parameter Immutability section does not mention temperature"
        )


# ---------------------------------------------------------------------------
# Group 3: No Hardcoded Models (Negative Tests)
# ---------------------------------------------------------------------------


class TestNoHardcodedModels:

    @pytest.mark.parametrize("doc_path", ENFORCEMENT_DOC_PATHS)
    def test_enforcement_docs_no_model_names(self, doc_path):
        """Enforcement docs must not contain hardcoded model names."""
        path = _rel(doc_path)
        assert os.path.exists(path), f"Enforcement doc missing: {doc_path}"
        content = open(path).read()
        matches = MODEL_NAME_RE.findall(content)
        assert not matches, (
            f"{doc_path} contains hardcoded model name(s): {matches}"
        )


# ---------------------------------------------------------------------------
# Group 4: Thresholds (preserved from original)
# ---------------------------------------------------------------------------


class TestThresholds:

    @pytest.mark.parametrize("tenant,threshold", [
        ("hotpotqa", "72.5%"),
        ("ifbench", "55.5%"),
        ("papillon", "93.5%"),
        ("hover", "60%"),
    ])
    def test_thresholds_in_playbooks(self, tenant, threshold):
        """Verify playbook thresholds match expected values."""
        playbook = _rel(f"tenants/{tenant}/docs/iteration-playbook.md")
        assert os.path.exists(playbook), f"Playbook missing: {playbook}"
        content = open(playbook).read()
        assert threshold in content, (
            f"{tenant} playbook missing threshold {threshold}. "
            f"Stop Criteria section: "
            f"{content[content.find('Stop Criteria'):content.find('Stop Criteria')+200]}"
        )

    @pytest.mark.parametrize("tenant,fragment", [
        ("hotpotqa", "72.5%"),
        ("ifbench", "55.5%"),
        ("papillon", "93.5%"),
        ("hover", "60%"),
    ])
    def test_derive_goal_extracts_threshold(self, tenant, fragment):
        """The derive_goal awk command extracts correct thresholds."""
        playbook = _rel(f"tenants/{tenant}/docs/iteration-playbook.md")
        result = subprocess.run(
            ["awk", '/^## Stop Criteria/{found=1; next} found && /^- /{sub(/^- /, ""); print; exit}',
             playbook],
            capture_output=True, text=True
        )
        assert fragment in result.stdout, (
            f"derive_goal for {tenant} returns '{result.stdout.strip()}', "
            f"missing '{fragment}'"
        )

    def test_hotpotqa_eval_operations_threshold(self):
        """HotpotQA eval-operations.md must also reflect the updated threshold."""
        path = _rel("tenants/hotpotqa/docs/eval-operations.md")
        content = open(path).read()
        assert "72.5%" in content, (
            "eval-operations.md still has old threshold. "
            f"Found: {content[content.find('Optimization target'):content.find('Optimization target')+100]}"
        )
