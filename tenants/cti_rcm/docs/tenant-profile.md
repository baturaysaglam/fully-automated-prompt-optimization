<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Tenant Profile

## Organization Profile
CTI-CWE is a public benchmark tenant for evaluating LLM ability to perform root cause mapping: given a CVE description, identify the correct CWE ID. Based on the CTIBench benchmark suite (AI4Sec/cti-bench, subset cti-rcm).

## Security Environment Assumptions
- Input: raw CVE descriptions from the NVD/MITRE ecosystem.
- Output: a single CWE ID (e.g., CWE-79).
- No access to external tools or databases during inference.

## Threat Model Focus
- Primary challenge: correctly identifying the root cause weakness from a vulnerability description that may describe symptoms, impacts, or attack vectors rather than the underlying weakness.

## Known Safe Patterns
- All CWE IDs follow the pattern `CWE-<digits>`.
- CVE descriptions are prefixed with "CVE Description: " by the data loader.

## Tenant Terminology
- **RCM**: Root Cause Mapping — the task of mapping CVE to CWE.
- **CTIBench**: Cyber Threat Intelligence Benchmark suite.
- **CWE**: Common Weakness Enumeration.
- **CVE**: Common Vulnerabilities and Exposures.
