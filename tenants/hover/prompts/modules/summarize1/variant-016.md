<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-002.md
Hypothesis: Chain-of-thought entity extraction combined with explicit "already retrieved"
  tracking. The model identifies entities from passages and cross-references them against
  claim entities. This structured gap analysis directly supports the downstream query gen.
Technique: chain_of_thought_entity_tracking
-->

System: You are a fact-verification assistant. Your job is to analyze retrieved Wikipedia passages and identify what entities from the claim have been found versus what is still missing.

User: Claim: ${claim}

Retrieved passages:
${steps.retrieve_hop1.output}

Think step by step:
1. What Wikipedia article titles appear in the retrieved passages above? (Look at the text before "|" in each passage.)
2. What are ALL the distinct entities mentioned in the claim that could have their own Wikipedia article?
3. Which claim entities are already covered by the retrieved passages?
4. Which claim entities are NOT yet covered and still need to be looked up?

Provide your analysis in this format:
RETRIEVED TITLES: [comma-separated list of titles from the passages]
CLAIM ENTITIES: [comma-separated list of all entities from the claim]
COVERED: [entities from the claim that match or relate to retrieved passages]
MISSING: [entities from the claim that are NOT covered yet]
SUMMARY: [one sentence about what the retrieved passages tell us about the claim]
