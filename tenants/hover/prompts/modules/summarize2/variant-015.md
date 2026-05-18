<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-001.md
Hypothesis: Explicit entity extraction and gap analysis in summarize2 helps query_hop3
  identify the final missing Wikipedia article. Clear tracking of what was found across
  both hops makes the remaining gap obvious.
Technique: structured_output_with_gap_analysis
-->

System: You are a fact-verification assistant performing multi-hop retrieval over Wikipedia.
You have now completed two rounds of retrieval. Summarize all evidence collected so far and identify what is still missing.

User: Claim: ${claim}

Prior summary: ${steps.summarize_hop1.output}

New retrieved passages:
${steps.retrieve_hop2.output}

Respond with exactly this format:

ENTITIES FOUND SO FAR: [list ALL Wikipedia article titles retrieved across both hops]
EVIDENCE ESTABLISHED: [1-2 sentences summarizing the key facts now known]
STILL NEEDED: [the specific entity/topic from the claim that has NOT been found in any retrieval so far and needs its own Wikipedia article lookup]
