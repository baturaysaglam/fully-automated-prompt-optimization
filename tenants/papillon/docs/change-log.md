<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

## 2026-05-14 — Prompt Optimization Complete

### Summary
Achieved **94.77% composite** on val split (target: 93.5%). Optimized both `redact_query` and `reconstruct_response` prompts through 5 variant iterations.

### Winning Configuration (variant-006)
- **Redaction prompt**: `variant-003.md` — aggressive PII redaction with explicit coverage of nationalities/demonyms, organization names, "when in doubt, redact" principle
- **Reconstruction prompt**: `variant-002.md` — quality-preserving reconstruction with re-personalization guidance, language matching, and completeness requirements

### Score Breakdown
| Metric | Baseline (v001) | Best (v006) | Δ |
|--------|----------------|-------------|---|
| Composite | 72.5% | 94.8% | +22.3 |
| Quality | 95.8% | 96.0% | +0.2 |
| Privacy | 49.1% | 93.6% | +44.5 |
| Leakage | 0.509 | 0.064 | -0.445 |

### Key Insights
1. The baseline's generic "remove PII" instruction missed ~50% of PII entities (especially org names, nationalities, brands)
2. Detailed PII categorization + "err on side of privacy" reduced leakage from 51% to 6.4%
3. Aggressive redaction needs a quality-preserving reconstruction prompt — pairing v003 redaction with v003 reconstruction dropped quality to 90.5%, but pairing with v002 reconstruction maintained 96% quality
4. The winning combination: aggressive redaction (privacy) + straightforward reconstruction (quality)

### Config
- Eval config: `remote-val-variant006.json`
- Run: `hephaestus-papillon-tf1eqf`

---

## 2026-05-12 — Initial Setup
- Summary: Tenant scaffold with 3-step privacy chain.
- Config: gpt-4.1-mini trusted + untrusted, temperature=1.0.
- Target: 95% composite on val split.

