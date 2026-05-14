<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Synthetic Example Requirements

Use these requirements when pruning noncompliant synthetic examples under a tenant synthetic examples root (for example, `tenants/<tenant_id>/datasets/synthetic_artifacts/`).

## Structure and Realism
- Each synthetic message should mirror realistic email structure: subject, greeting, signature.
- Use credible phishing TTPs and believable tenant/partner references when appropriate.
- Avoid implausible or random strings that break realism.
- Missing-body examples are allowed when intentionally used as hard cases.

## File Structure
Each example directory should include:
- `Prompt.pdf.txt`
- `Context - Tools.pdf.txt`
- `Context - Stealth Watch.pdf.txt`
- `Context - Email Body.pdf.txt` or `Context - No Email Body.pdf.txt`
- `Summary.pdf.txt`

## Labeling
- Keep `labels_review.csv` and `hard_labels_review.csv` aligned to `Summary.pdf.txt` and existing example directories.

## Hashes
- `attachments_sha256` must be realistic 64-hex values, not placeholders (e.g., all A/B/0 strings).
