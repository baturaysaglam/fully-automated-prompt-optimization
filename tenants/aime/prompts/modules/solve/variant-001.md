<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: Your input fields are:
1. `problem` (str):
Your output fields are:
1. `reasoning` (str):
2. `answer` (str):
All interactions will be structured in the following way, with the appropriate values filled in.

[[ ## problem ## ]]
{problem}

[[ ## reasoning ## ]]
{reasoning}

[[ ## answer ## ]]
{answer}

[[ ## completed ## ]]
In adhering to this structure, your objective is:
        Solve the problem and provide the answer in the correct format.

User: [[ ## problem ## ]]
${problem}

Respond with the corresponding output fields, starting with the field `[[ ## reasoning ## ]]`, then `[[ ## answer ## ]]` (an integer with no other text), and then ending with the marker for `[[ ## completed ## ]]`.
