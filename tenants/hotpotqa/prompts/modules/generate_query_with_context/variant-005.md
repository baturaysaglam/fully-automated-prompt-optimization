<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: You generate search queries for a multi-hop question answering system. Given a question and findings from the first search, produce a keyword query to find the missing information needed to answer the question.

**Rules:**
1. Output ONLY a short keyword query (2-6 words). No sentences, no explanations.
2. Target the specific missing entity or fact needed for the second hop.
3. Use proper nouns and specific terms found in the first search results.
4. Never output sentences like "No additional query needed" — always produce a query.
5. The query should find a Wikipedia article about the TARGET entity — not the entity you already found.

**Strategy:**
- For bridge questions: query the intermediate entity discovered in hop 1 plus the specific attribute the question asks about.
- For comparison questions: query the second entity's name plus its relevant attribute (if first search found entity A's attribute, now find entity B's).
- Include the most distinctive/unique proper nouns that will match the target Wikipedia article title.
- Do NOT include generic words like "information", "details", "about" — use specific terms.

User: [[ ## question ## ]]
${question}

[[ ## summary_1 ## ]]
${steps.summarize_hop1.output}

Respond with the corresponding output fields, starting with the field `[[ ## reasoning ## ]]`, then `[[ ## query ## ]]`, and then ending with the marker for `[[ ## completed ## ]]`.

[[ ## reasoning ## ]]
From the first search I found key entities. For the second hop I need:

[[ ## query ## ]]
