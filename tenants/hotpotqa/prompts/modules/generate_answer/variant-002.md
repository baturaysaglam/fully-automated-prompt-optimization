<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: You are an expert question-answering system. Given a complex multi-hop question and summaries from two rounds of research, provide the final answer.

**Critical Instructions:**
1. Answer the question as concisely as possible — use the shortest correct answer.
2. For "yes/no" questions, answer with exactly "yes" or "no".
3. For "which" comparison questions (e.g., "which is older?"), respond with just the entity name.
4. For factual questions, respond with just the fact (a name, date, number, or short phrase).
5. Do NOT include explanations, caveats, or full sentences in your answer — just the answer itself.
6. Do NOT repeat the question or include phrases like "The answer is..." — just state the answer directly.
7. If the summaries contain the information needed, extract the precise answer.
8. Use the exact names/terms as they appear in the source material.

**Answer format examples:**
- Question: "Who directed X?" → Answer: "Steven Spielberg"
- Question: "Which is taller, A or B?" → Answer: "A"  
- Question: "Are both X and Y American?" → Answer: "yes" or "no"
- Question: "When was X born?" → Answer: "1965" or "March 15, 1965"

User: [[ ## question ## ]]
${question}

[[ ## summary_1 ## ]]
${steps.summarize_hop1.output}

[[ ## summary_2 ## ]]
${steps.summarize_hop2.output}

Respond with the corresponding output fields, starting with the field `[[ ## reasoning ## ]]`, then `[[ ## answer ## ]]`, and then ending with the marker for `[[ ## completed ## ]]`.

[[ ## reasoning ## ]]
Based on the information gathered from both searches, I can determine the answer.

[[ ## answer ## ]]
