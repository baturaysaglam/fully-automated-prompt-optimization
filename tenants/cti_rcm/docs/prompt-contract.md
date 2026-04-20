<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Prompt Contract

## Output Format Contract
- The model must output a CWE ID on the last line of its response.
- Accepted formats: `CWE-<digits>` (proper) or `CWE: <digits>` / `ID: <digits>` (improper).
- The scorer uses faith's `SequentialMatcher` with `match_if_unique` disambiguation.

## Decision Policy
- The model should analyze the CVE description, identify the root cause weakness, and map it to the most specific applicable CWE ID.
- When multiple CWEs could apply, the model should choose the most specific one.

## Defang and Safety Rules
- No URL defanging needed — inputs are plain-text CVE descriptions.
- No PII or sensitive data in the dataset.

## Variant Strategy
- Variants stored in `prompts/variants/variant-NNN.md`.
- `variant-001.md`: baseline from faith's `chat_inst_template`.
- Iterate on system instructions, output format guidance, and reasoning depth.

## Non-Goals
- Multi-label CWE mapping (only one CWE per case).
- CVSS scoring or severity assessment.
- Generating CVE descriptions or CWE definitions.
