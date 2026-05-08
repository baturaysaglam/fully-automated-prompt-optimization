<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: Your input fields are:
1. `user_query` (str):
Your output fields are:
1. `reasoning` (str):
2. `llm_request` (str):
All interactions will be structured in the following way, with the appropriate values filled in.

[[ ## user_query ## ]]
{user_query}

[[ ## reasoning ## ]]
{reasoning}

[[ ## llm_request ## ]]
{llm_request}

[[ ## completed ## ]]
In adhering to this structure, your objective is:
        Given a private user query, create a privacy-preserving request for a powerful external LLM. The LLM may assist without learning private information about the user.

User: [[ ## user_query ## ]]
${user_query}

Respond with the corresponding output fields, starting with the field `[[ ## reasoning ## ]]`, then `[[ ## llm_request ## ]]`, and then ending with the marker for `[[ ## completed ## ]]`.
