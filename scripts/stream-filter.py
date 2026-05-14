#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Filter for claude --output-format stream-json.

Reads newline-delimited JSON events from stdin and prints human-readable
summaries of assistant text and tool calls to stdout.
"""
import json
import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        evt = json.loads(line)
    except json.JSONDecodeError:
        continue
    etype = evt.get("type", "")
    if etype == "assistant" and evt.get("message", {}).get("content"):
        for block in evt["message"]["content"]:
            if block.get("type") == "text" and block.get("text"):
                print(block["text"], flush=True)
            elif block.get("type") == "tool_use":
                print(f"  -> {block.get('name', '?')}()", flush=True)
