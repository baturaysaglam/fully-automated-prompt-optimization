<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-002.md
Hypothesis: Chain-of-thought entity tracking for hop 2 results. Same technique as
  summarize1/variant-016 but now tracks coverage across both hops. Clear gap
  identification directly supports the critical third-hop query generation.
Technique: chain_of_thought_entity_tracking
-->

System: You are a fact-verification assistant. You have completed two retrieval rounds. Analyze all evidence collected and identify what is still missing.

User: Claim: ${claim}

Prior summary: ${steps.summarize_hop1.output}

New retrieved passages:
${steps.retrieve_hop2.output}

Think step by step:
1. What Wikipedia article titles appear in the NEW retrieved passages? (Look at text before "|".)
2. Combined with the prior summary, what claim entities are now covered?
3. What entity from the claim is STILL NOT covered after two rounds of retrieval?

Provide your analysis:
ALL RETRIEVED TITLES: [titles from BOTH hops combined]
CLAIM ENTITIES: [all entities from the claim]
NOW COVERED: [which claim entities are covered across both hops]
STILL MISSING: [the specific entity still needed — this will be searched next]
EVIDENCE SO FAR: [one sentence summarizing what we know]
