# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""
Verification tests for experiment configuration:
- Temperature=0.0 across all tenants
- CoT prompting in effect for IFBench and HoVer
- Threshold values correctly set in playbooks
"""

import glob
import json
import os
import subprocess

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rel(path):
    return os.path.join(PROJECT_ROOT, path)


class TestTemperatureZero:

    def test_all_configs_temperature_zero(self):
        """Every provider_settings.temperature must be 0.0."""
        configs = glob.glob(_rel("tenants/*/configs/*.json"))
        assert len(configs) > 0, "No config files found"
        for path in configs:
            with open(path) as f:
                config = json.load(f)
            if "provider_settings" in config:
                temp = config["provider_settings"].get("temperature")
                assert temp == 0.0, (
                    f"{os.path.relpath(path, PROJECT_ROOT)}: "
                    f"temperature is {temp}, expected 0.0"
                )

    def test_papillon_untrusted_model_temperature_preserved(self):
        """Papillon untrusted_model.temperature must remain 1.0 (adversarial)."""
        configs = glob.glob(_rel("tenants/papillon/configs/*.json"))
        for path in configs:
            with open(path) as f:
                config = json.load(f)
            chain_config = config.get("chain", {}).get("config", {})
            if "untrusted_model" in chain_config:
                temp = chain_config["untrusted_model"].get("temperature")
                assert temp == 1.0, (
                    f"{os.path.relpath(path, PROJECT_ROOT)}: "
                    f"untrusted_model temperature is {temp}, must stay 1.0"
                )


class TestIFBenchCoT:

    def test_generate_variant002_exists(self):
        """IFBench generate variant-002 must exist."""
        path = _rel("tenants/ifbench/prompts/modules/generate/variant-002.md")
        assert os.path.exists(path), f"CoT generate variant missing: {path}"

    def test_generate_has_cot_markers(self):
        """IFBench generate variant-002 must contain CoT output markers."""
        path = _rel("tenants/ifbench/prompts/modules/generate/variant-002.md")
        content = open(path).read()
        assert "---RESPONSE---" in content, "Generate prompt missing ---RESPONSE--- separator"
        assert "CONSTRAINTS" in content, "Generate prompt missing CONSTRAINTS instruction"
        assert "PLAN" in content, "Generate prompt missing PLAN instruction"

    def test_generate_does_not_suppress_reasoning(self):
        """Generate must NOT suppress CoT output."""
        path = _rel("tenants/ifbench/prompts/modules/generate/variant-002.md")
        content = open(path).read()
        body = content.split("-->", 1)[-1] if "-->" in content else content
        assert "output ONLY" not in body, "Generate prompt suppresses CoT output"
        assert "no meta-commentary" not in body.lower(), "Generate prompt suppresses reasoning"

    def test_verify_variant002_exists(self):
        """IFBench verify variant-002 must exist."""
        path = _rel("tenants/ifbench/prompts/modules/verify/variant-002.md")
        assert os.path.exists(path), f"CoT verify variant missing: {path}"

    def test_verify_handles_separator(self):
        """IFBench verify variant-002 must reference the ---RESPONSE--- separator."""
        path = _rel("tenants/ifbench/prompts/modules/verify/variant-002.md")
        content = open(path).read()
        assert "---RESPONSE---" in content, "Verify prompt doesn't reference separator"
        assert "${steps.generate.output}" in content, "Verify doesn't receive generate output"

    def test_config_points_to_cot_variants(self):
        """IFBench eval config must point to CoT variants (variant-002)."""
        path = _rel("tenants/ifbench/configs/local-chain-variant002.json")
        assert os.path.exists(path), f"CoT eval config missing: {path}"
        with open(path) as f:
            config = json.load(f)
        paths = config["chain"]["config"]["prompt_paths"]
        assert "variant-002" in paths["generate"], (
            f"Config generate points to {paths['generate']}, not variant-002"
        )
        assert "variant-002" in paths["verify"], (
            f"Config verify points to {paths['verify']}, not variant-002"
        )

    def test_config_temperature_zero(self):
        """IFBench CoT config must use temperature=0.0."""
        path = _rel("tenants/ifbench/configs/local-chain-variant002.json")
        with open(path) as f:
            config = json.load(f)
        assert config["provider_settings"]["temperature"] == 0.0


class TestHoVerCoT:

    def test_summarize1_variant002_exists(self):
        """HoVer summarize1 variant-002 must exist."""
        path = _rel("tenants/hover/prompts/modules/summarize1/variant-002.md")
        assert os.path.exists(path), f"CoT variant missing: {path}"

    def test_summarize2_variant002_exists(self):
        """HoVer summarize2 variant-002 must exist."""
        path = _rel("tenants/hover/prompts/modules/summarize2/variant-002.md")
        assert os.path.exists(path), f"CoT variant missing: {path}"

    def test_summarize_has_cot_reasoning(self):
        """HoVer summarize variants must contain CoT reasoning structure."""
        for module in ["summarize1", "summarize2"]:
            path = _rel(f"tenants/hover/prompts/modules/{module}/variant-002.md")
            content = open(path).read()
            assert "SEARCH:" in content, f"{module} missing SEARCH: output marker"
            assert "step by step" in content.lower() or "reasoning" in content.lower(), (
                f"{module} missing CoT reasoning instruction"
            )

    def test_summarize_does_not_suppress_reasoning(self):
        """Summarize nodes must externalize reasoning (not suppress it)."""
        for module in ["summarize1", "summarize2"]:
            path = _rel(f"tenants/hover/prompts/modules/{module}/variant-002.md")
            content = open(path).read()
            body = content.split("-->", 1)[-1] if "-->" in content else content
            lines_lower = body.lower()
            if "output only" in lines_lower:
                assert "SEARCH" in body, f"{module} suppresses reasoning output"

    def test_query_nodes_no_cot(self):
        """HoVer query nodes must NOT have CoT (output goes directly to BM25)."""
        for module in ["query_hop2", "query_hop3"]:
            path = _rel(f"tenants/hover/prompts/modules/{module}/variant-002.md")
            if os.path.exists(path):
                content = open(path).read()
                assert "step by step" not in content.lower(), (
                    f"{module} has CoT but output goes directly to BM25!"
                )

    def test_config_points_to_cot_summarize_and_baseline_query(self):
        """HoVer eval config must use CoT summarize variants + baseline query variants."""
        path = _rel("tenants/hover/configs/local-chain-variant002.json")
        assert os.path.exists(path), f"CoT eval config missing: {path}"
        with open(path) as f:
            config = json.load(f)
        paths = config["chain"]["config"]["prompt_paths"]
        assert "variant-002" in paths["summarize1"], "summarize1 not pointing to CoT variant"
        assert "variant-002" in paths["summarize2"], "summarize2 not pointing to CoT variant"
        assert "variant-001" in paths["query_hop2"], "query_hop2 should use baseline variant-001"
        assert "variant-001" in paths["query_hop3"], "query_hop3 should use baseline variant-001"

    def test_config_temperature_zero(self):
        """HoVer CoT config must use temperature=0.0."""
        path = _rel("tenants/hover/configs/local-chain-variant002.json")
        with open(path) as f:
            config = json.load(f)
        assert config["provider_settings"]["temperature"] == 0.0


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
