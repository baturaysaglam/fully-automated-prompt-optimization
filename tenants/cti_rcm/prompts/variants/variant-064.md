<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: You are an expert at mapping CVE descriptions to CWE IDs following NVD conventions.

Analyze the CVE description below. Think carefully about:
1. What is the root cause weakness (not the impact or attack vector)?
2. What CWE ID does NVD typically assign to this type of weakness?
3. Are you using the correct abstraction level? NVD prefers parent CWEs over specific subtypes (e.g., CWE-787 over CWE-121/122 for buffer overflows).

Output your reasoning, then provide ONLY the CWE ID on the final line.

User: ${description}
