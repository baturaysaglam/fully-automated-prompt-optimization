<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: Your input fields are:
1. `related_llm_request` (str):
2. `related_llm_response` (str): information from a powerful LLM responding to a related request
3. `user_query` (str): the user's request you need to fulfill
Your output fields are:
1. `reasoning` (str):
2. `response` (str): your final response to the user's request
All interactions will be structured in the following way, with the appropriate values filled in.

[[ ## related_llm_request ## ]]
{related_llm_request}

[[ ## related_llm_response ## ]]
{related_llm_response}

[[ ## user_query ## ]]
{user_query}

[[ ## reasoning ## ]]
{reasoning}

[[ ## response ## ]]
{response}

[[ ## completed ## ]]
In adhering to this structure, your objective is:
        Respond to a user query. For inspiration, we found a potentially related request to a powerful external LLM and its response.

User: [[ ## related_llm_request ## ]]
${steps.craft_redacted_request.output}

[[ ## related_llm_response ## ]]
${steps.untrusted_llm.output}

[[ ## user_query ## ]]
${user_query}

Respond with the corresponding output fields, starting with the field `[[ ## reasoning ## ]]`, then `[[ ## response ## ]]`, and then ending with the marker for `[[ ## completed ## ]]`.
