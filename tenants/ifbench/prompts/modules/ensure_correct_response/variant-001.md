<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: Your input fields are:
1. `query` (str):
2. `response` (str):
Your output fields are:
1. `reasoning` (str):
2. `final_response` (str):
All interactions will be structured in the following way, with the appropriate values filled in.

[[ ## query ## ]]
{query}

[[ ## response ## ]]
{response}

[[ ## reasoning ## ]]
{reasoning}

[[ ## final_response ## ]]
{final_response}

[[ ## completed ## ]]
In adhering to this structure, your objective is:
        Ensure the response is correct and adheres to the given constraints. Your response will be used as the final response.

User: [[ ## query ## ]]
${prompt}

[[ ## response ## ]]
${steps.generate_response.output}

Respond with the corresponding output fields, starting with the field `[[ ## reasoning ## ]]`, then `[[ ## final_response ## ]]`, and then ending with the marker for `[[ ## completed ## ]]`.
