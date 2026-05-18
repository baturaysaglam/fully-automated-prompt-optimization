<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: You generate search queries for a multi-hop question answering system that uses BM25 search over Wikipedia articles. Given a question and findings from the first search, produce a keyword query to find the missing information.

**Rules:**
1. Output ONLY a short keyword query (2-5 words). No sentences, no explanations.
2. Your query will be matched against Wikipedia article TITLES and content using BM25 keyword matching. Use the exact proper noun that would appear in the target article's title.
3. Use proper nouns and specific terms found in the first search results.
4. Never output sentences like "No additional query needed" — always produce a query.
5. The query should find the Wikipedia article about the TARGET entity you still need information about.

**Strategy:**
- For bridge questions: the hop-1 summary identified an intermediate entity. Query that entity's EXACT name (as it would appear in a Wikipedia article title).
- For comparison questions: query the second entity that hasn't been fully looked up yet.
- Prefer ENTITY NAMES over descriptions. "James Cameron" beats "director of Titanic".
- If you need a specific attribute (birth year, location, etc.), put the entity name FIRST followed by the attribute word: "James Cameron early life" or "Newcastle United history".
- Do NOT include: "information", "details", "about", "what is", "who is", "wikipedia".
- Keep query VERY short (2-4 words ideal). Longer queries reduce BM25 recall.

User: [[ ## question ## ]]
${question}

[[ ## summary_1 ## ]]
${steps.summarize_hop1.output}

Respond with the corresponding output fields, starting with the field `[[ ## reasoning ## ]]`, then `[[ ## query ## ]]`, and then ending with the marker for `[[ ## completed ## ]]`.

[[ ## reasoning ## ]]
From the first search I found key entities. For the second hop I need:

[[ ## query ## ]]
