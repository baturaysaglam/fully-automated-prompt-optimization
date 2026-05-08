# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Instrumentation for Claude Code sub-agent invocations during ``/optimization`` runs.

Modules:
  - ``call_tracker``: ``CallEvent`` dataclass, atomic-append writer, summarizer.
  - ``call_tracker_hook``: entry point for Claude Code ``SubagentStart`` /
    ``SubagentStop`` hooks, configured in ``.claude/settings.json``.
"""
