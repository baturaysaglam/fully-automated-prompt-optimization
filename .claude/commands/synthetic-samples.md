<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

---
description: >
  Create realistic synthetic examples for eval dataset augmentation.
  TRIGGER when: user wants to create synthetic test cases, add edge cases, augment eval datasets, expand test coverage, create hard cases, or generate new evaluation examples.
  DO NOT TRIGGER when: user is pruning/cleaning existing synthetic data (use synthetic-pruner), running evals (use eval-runner), or optimizing prompts (use optimization agent).
---

# Synthetic Samples

## Scope
- Create realistic synthetic examples under a tenant synthetic examples root (for example, `tenants/<tenant_id>/datasets/synthetic_artifacts/`).
- Keep customer/source artifacts untouched (`tenants/*/source_artifacts/`).
- Produce review CSVs for model-assisted labeling.
- Keep all content synthetic and non-attributable. No real customer names, domains, or IPs.

## Quick Start Workflow
1. Pick a scenario type: benign, phishing, credential theft, BEC, malware delivery, or false positive.
2. Choose a naming pattern and create the example directory.
3. Populate context files using the templates below.
4. Write `Summary.pdf.txt` with explicit labels that match CSV heuristics.
5. Add/refresh `labels_review.csv` or `hard_labels_review.csv` entries.

## Standard Example Structure
Each example directory should include:
- `Prompt.pdf.txt` (placeholder or template reference)
- `Context - Tools.pdf.txt` (copy from a tenant baseline example if available)
- `Context - Stealth Watch.pdf.txt`
- `Context - Email Body.pdf.txt` or `Context - No Email Body.pdf.txt`
- `Summary.pdf.txt` (explicit label language)

## Naming
- Regular: `Example N - <Descriptor>`
- Hard cases: `Hard Example N - <Descriptor>`

## Labeling Workflow
1. Propose labels in a CSV (`labels_review.csv` or `hard_labels_review.csv`).
2. Keep labels aligned with `Summary.pdf.txt` text so existing heuristics extract GT.
3. If a file is removed, update both CSVs so row counts and filenames stay aligned.

## Telemetry Patterning
- Use realistic fields appropriate to the telemetry source (e.g., `source_name`, `observation_name`, `severity`, `tactic_ids`, `technique_ids`).
- For email-related scenarios, include fields like `email_direction`, `email_from`, `email_to`, `subject`, and `attachments_sha256`.
- For hard cases, include conflicting signals and add `message_direction` and `threat_category` when useful.
- Keep timestamps in ISO 8601 with timezone offsets.
- Use believable internal domains like `<internal_domain>` or `<tenant_internal_domain>`.
- Use external domains that look plausible but are synthetic (e.g., `secure-docs[.]support`, `billing-portal[.]services`).

## IOC Menu (Phishing)
Pick 1-3 per example, consistent with scenario.
- Domains: `payroll-secure.support`, `adobe-signin.services`, `microsoft-auth[.]cloud`, `sharepoint-docs[.]support`, `finance-portal-support.com`
- URLs: `hxxps://payroll-secure.support/login`, `hxxps://adobe-signin.services/doc/18923`, `hxxps://sharepoint-docs.support/s/finance`, `hxxps://microsoft-auth.cloud/verify`
- IPs: `185.199.110.45`, `203.0.113.17`, `198.51.100.91`, `192.0.2.54`
- Email addresses: `notice@payroll-secure.support`, `support@adobe-signin.services`, `security@microsoft-auth.cloud`
- File hashes (sha256): `6c2eaa5f3a2b9e9f5c4d2c1a0b9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e`, `9f1e0d2c3b4a5f6e7d8c9b0a1e2d3c4b5a6f7e8d9c0b1a2c3d4e5f6a7b8c9d0`

## Hard Case Patterns
Use to stump the prompt:
- Internal direction but external domain
- External direction with internal domain (spoofing)
- High severity + benign description
- Missing body + conflicting indicators
- Summary says false positive but telemetry says scam/bec
- Internal forward of external phish
