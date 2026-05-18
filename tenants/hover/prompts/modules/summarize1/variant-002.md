<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-001.md
Hypothesis: Explicit Chain-of-Thought reasoning before the search query matches
  GEPA's dspy.ChainOfThought("claim,passages->summary") structure. Model must
  externalize its entity analysis before committing to a search query.
Technique: chain_of_thought
-->

System: You determine what Wikipedia article to search for next in a multi-hop fact
verification task. You MUST show your reasoning before giving your final answer.

User: Claim: ${claim}

Retrieved passages:
${steps.retrieve_hop1.output}

Think step by step:

**Already retrieved:** List the article titles visible above (text before "|" in each passage).
**Claim entities:** List every entity in the claim that should have its own Wikipedia article.
**Gap analysis:** Which claim entities are NOT among the retrieved titles?
**Decision:** Pick the single most important missing entity.

After your reasoning, output your search query on a line starting with SEARCH:

SEARCH: [entity name]
