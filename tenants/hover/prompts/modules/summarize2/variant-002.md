<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-001.md
Hypothesis: Explicit Chain-of-Thought reasoning before the third-hop search query.
  Model must externalize its gap analysis across two rounds of evidence before
  committing to the final search query.
Technique: chain_of_thought
-->

System: You determine what Wikipedia article to search for next in a multi-hop fact
verification task. You have already retrieved two rounds of passages. You MUST show
your reasoning before giving your final answer.

User: Claim: ${claim}

Prior summary: ${steps.summarize_hop1.output}

New retrieved passages:
${steps.retrieve_hop2.output}

Think step by step:

**Evidence so far:** Summarize what facts from hop 1 and hop 2 are established.
**Claim requirements:** What does the claim assert that still needs verification?
**Gap analysis:** What entity or fact is still missing to fully verify or refute the claim?
**Decision:** Pick the single most important missing entity to search for.

After your reasoning, output your search query on a line starting with SEARCH:

SEARCH: [entity name]
