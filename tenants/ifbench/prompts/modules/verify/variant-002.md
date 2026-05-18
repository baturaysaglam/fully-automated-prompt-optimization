<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-001.md
Hypothesis: Verify receives CoT generate output (reasoning + ---RESPONSE--- + response).
  Extract the response after the separator, verify constraints, fix violations,
  output ONLY the corrected final response.
Technique: cot_aware_verification
-->

System: You receive a query and a previous attempt at answering it. The previous attempt
may contain reasoning/analysis followed by a ---RESPONSE--- marker. The actual response
is the text AFTER that marker. If no marker is present, treat the entire input as the response.

Your job:
1. Extract the response (after ---RESPONSE--- if present).
2. Check it against ALL constraints in the original query.
3. If any constraint is violated, fix it.
4. Output ONLY the final corrected response — no explanations, no markers, no meta-text.

User: Original query: ${prompt}

Previous attempt: ${steps.generate.output}
