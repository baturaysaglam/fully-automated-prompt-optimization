<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: Your input fields are:
1. `query` (str):
Your output fields are:
1. `reasoning` (str):
2. `response` (str):
All interactions will be structured in the following way, with the appropriate values filled in.

[[ ## query ## ]]
{query}

[[ ## reasoning ## ]]
{reasoning}

[[ ## response ## ]]
{response}

[[ ## completed ## ]]
In adhering to this structure, your objective is:
        Respond to the query.

User: [[ ## query ## ]]
${prompt}

Respond with the corresponding output fields, starting with the field `[[ ## reasoning ## ]]`, then `[[ ## response ## ]]`, and then ending with the marker for `[[ ## completed ## ]]`.
