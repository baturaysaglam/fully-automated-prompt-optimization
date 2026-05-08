<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Bigger-Model Call Tracking

## Why

We want to compare FEPO against GEPA on a fair footing. GEPA reports exact
counts of "reflector" (bigger-model) calls per benchmark (e.g., 69 on
HotpotQA). To claim that FEPO's Claude Code pipeline uses the bigger model
less than or equal to GEPA, we need to count every Opus/Sonnet invocation
during a FEPO `/optimization` run.

## How it works

- Claude Code's `SubagentStart` and `SubagentStop` hooks fire when any
  sub-agent (`optimization`, `variant-reviewer`, `step-attribution`, etc.)
  starts or finishes during a session. See `docs.claude.com/docs/en/hooks.md`.
- `.claude/settings.json` (committed at repo root) wires those events to:
  `python -m src.hephaestus.optimization.call_tracker_hook {start|end}`.
- The hook script reads the hook payload from **stdin** (JSON), parses the
  acting subagent's `.claude/agents/<name>.md` frontmatter to resolve its
  `model:` field (dynamic — single source of truth), and appends one
  `CallEvent` to `tenants/<tenant>/evals/<run>/optimization-calls.jsonl`.
- `run_id` is read from `.claude/state/current_run_id`; `tenant_id` from
  `.claude/state/current_tenant_id`. Both files are written by the
  orchestrator agent's bootstrap routine (see
  `.claude/agents/optimization.md` "Call Tracking Bootstrap" section).
- If either state file is missing, output falls back to
  `tenants/_unscoped/evals/ambient/optimization-calls.jsonl`. Hook errors
  are logged to `tenants/_unscoped/evals/ambient/hook_errors.log` and never
  raised (the hook must not block `/optimization`).

## Event schema

One JSON object per line of `optimization-calls.jsonl`:

```json
{
  "timestamp": "2026-05-08T14:22:01.123Z",
  "run_id": "abc123",
  "tenant_id": "hotpotqa",
  "layer": "orchestrator",
  "subagent": "optimization",
  "model_family": "opus",
  "model_id": "opus",
  "event": "invocation_start",
  "invocation_id": "ulid-or-uuid",
  "parent_invocation_id": null,
  "input_tokens": null,
  "output_tokens": null,
  "duration_ms": null
}
```

`invocation_start` and `invocation_end` events share an `invocation_id`.
Token + duration fields are only populated on `invocation_end` (and only
when the Claude Code hook payload includes them).

## Summarizing a run

```
python scripts/summarize_optimization_calls.py --run abc123 --tenant hotpotqa
```

Outputs a JSON block suitable for appending to
`tenants/<tenant>/docs/iteration-memory.jsonl`:

```json
{
  "iteration_id": "abc123",
  "tenant_id": "hotpotqa",
  "bigger_model_calls": {
    "total": 147,
    "by_subagent": {"optimization": 89, "variant-reviewer": 12, "step-attribution": 46},
    "by_layer": {"orchestrator": 89, "subagent": 58},
    "by_model_family": {"opus": 101, "sonnet": 46},
    "by_model_id": {"opus": 101, "sonnet": 46},
    "tokens": {"input": 1234567, "output": 234567},
    "duration_ms_total": 3456789
  }
}
```

## Useful `jq` snippets

Count invocations by subagent:
```
jq -s 'map(select(.event == "invocation_start")) | group_by(.subagent) | map({key:.[0].subagent,count:length})' \
  tenants/hotpotqa/evals/abc123/optimization-calls.jsonl
```

Latency per subagent (requires `invocation_end` events with `duration_ms`):
```
jq -s 'map(select(.event == "invocation_end" and .duration_ms)) | group_by(.subagent) | map({sub:.[0].subagent,ms_total:(map(.duration_ms) | add)})' \
  tenants/hotpotqa/evals/abc123/optimization-calls.jsonl
```

## Comparison vs GEPA

GEPA's reflector calls correspond to FEPO's `opus` + `sonnet` calls. Report
`by_model_family` as the direct comparison axis. Note that FEPO's
orchestrator is itself an Opus call; GEPA's reflector is invoked from a
non-LLM python harness, so the orchestrator count is FEPO-specific
overhead and should be separately documented in the paper's Evaluation
section.

## Non-goals

- **No budget cap**. The tracker does not enforce limits. A cap, if needed,
  is a separate feature that would likely live in the orchestrator agent's
  system prompt, not in the hook.
- **No real-time UX**. This is post-hoc instrumentation for fair comparison;
  live monitoring is out of scope.

## Troubleshooting

- **`optimization-calls.jsonl` is empty** after a run: the orchestrator
  forgot to write `.claude/state/current_run_id` / `current_tenant_id`. The
  hook then writes to `tenants/_unscoped/evals/ambient/` instead; look there.
- **Hook errors**: see `tenants/_unscoped/evals/ambient/hook_errors.log`.
  Common causes: malformed stdin payload, agent frontmatter with
  non-standard layout.
- **Wrong `model_family`**: check the target subagent's
  `.claude/agents/<name>.md` frontmatter — the `model:` field is the single
  source of truth. If frontmatter is absent or the value is unknown, events
  are tagged `model_family: unknown`.
- **Multiple sessions interleave**: the current log does not distinguish
  between concurrent orchestrator sessions. In practice, FEPO runs one
  orchestrator per shell; this is an intentional simplification.
