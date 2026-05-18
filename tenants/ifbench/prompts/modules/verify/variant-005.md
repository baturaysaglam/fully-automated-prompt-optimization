<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-027 (from pods scoring 50-61%, minimal verify approach)
Hypothesis: The minimal "pass-through + minor fix" verify approach outperforms
  aggressive rewriting verifiers. Recreate variant-027 exactly.
Technique: minimal_passthrough
-->

System: Below is a response to a query. Your job is to output it. If you notice an obvious constraint violation (wrong keyword count, missing format requirement), you may fix it — but only if you are highly confident the fix is correct. Otherwise, output the response unchanged.

User: Query: ${prompt}

Response to output: ${steps.generate.output}
