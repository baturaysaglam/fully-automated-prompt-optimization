<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-044 (from pod tf1583, 61% on 245/294 cases)
Hypothesis: Replicate variant-044 approach (explicit constraint listing + counting + verification)
  which scored 61% before the run failed. This is an exact recreation.
Technique: explicit_count_verify
-->

System: Respond to the query below. You must follow ALL constraints exactly.

Step 1: List every constraint you find.
Step 2: For each constraint, note the EXACT requirement (e.g., "keyword X must appear exactly 3 times", "response must be 71-73 words", "first word must be a verb").
Step 3: Write a draft response that attempts to satisfy all constraints.
Step 4: Verify EACH constraint against your draft:
  - Count every keyword occurrence explicitly
  - Count total words if a range is specified
  - Check the first word if specified
  - Check formatting requirements
Step 5: If ANY constraint fails verification, rewrite the failing part and verify again.
Step 6: Output your verified response after "---" on its own line.

User: ${prompt}
