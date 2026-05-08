<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: Your input fields are:
1. `claim` (str):
2. `summary_1` (str):
3. `summary_2` (str):
Your output fields are:
1. `reasoning` (str):
2. `query` (str):
All interactions will be structured in the following way, with the appropriate values filled in.

[[ ## claim ## ]]
{claim}

[[ ## summary_1 ## ]]
{summary_1}

[[ ## summary_2 ## ]]
{summary_2}

[[ ## reasoning ## ]]
{reasoning}

[[ ## query ## ]]
{query}

[[ ## completed ## ]]
In adhering to this structure, your objective is:
        Given the fields `claim`, `summary_1`, `summary_2`, produce the fields `query`.

User: [[ ## claim ## ]]
${claim}

[[ ## summary_1 ## ]]
${steps.summarize_hop1.output}

[[ ## summary_2 ## ]]
${steps.summarize_hop2.output}

Respond with the corresponding output fields, starting with the field `[[ ## reasoning ## ]]`, then `[[ ## query ## ]]`, and then ending with the marker for `[[ ## completed ## ]]`.
