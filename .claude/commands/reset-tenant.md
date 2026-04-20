<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

---
description: >
  Reset a tenant to baseline (variant-001), removing all optimization artifacts.
  TRIGGER when: user wants to reset a tenant, start fresh, clear optimization history,
  revert to baseline, undo all prompt iterations, or clean-slate a tenant.
  DO NOT TRIGGER when: user wants to run evals (use eval-runner), optimize prompts
  (use optimization agent), or create synthetic data (use synthetic-samples).
---

# Reset Tenant to Baseline

## Overview

Remove all optimization artifacts (non-baseline prompt variants, chain variants, iteration memory, optimization changelog entries) from a tenant, leaving it in a clean baseline state as if no optimization had ever been performed. Git history preserves the work.

## Inputs

- `tenant_id` (required): The tenant directory name under `tenants/`. If not provided, ask the user.

## Pre-flight

1. **Validate tenant exists**: Confirm `tenants/<tenant_id>/` exists. Abort if not.

2. **Detect prompt layout** (per-tenant, not assumed globally):
   - **Modules layout**: `tenants/<tenant_id>/prompts/modules/` exists and contains subdirectories with variant files (e.g. hotpotqa)
   - **Flat layout**: `tenants/<tenant_id>/prompts/variants/` contains variant files directly (e.g. aime2025, cti_rcm)
   - If neither directory exists, warn and skip prompt variant cleanup.

3. **Inventory what will be reset** — scan and list:
   - Non-baseline prompt variants (`variant-002` and above) in whichever layout applies
   - Chain variant files in `chains/variants/` (if directory exists)
   - Config files referencing non-baseline variants in `configs/`
   - Changelog entries in `docs/change-log.md` referencing `variant-002` or higher
   - Iteration memory in `docs/iteration-memory.jsonl` (if it exists and is non-empty)
   - Local eval outputs in `evals/tmp/` and `reports/` (if they exist)

4. **Show the inventory to the user** and ask for explicit confirmation before proceeding. If there is nothing to reset, report that the tenant is already at baseline and stop.

## Procedure

All paths below are relative to `tenants/<tenant_id>/`.

### Step 1: Snapshot commit

If there are any uncommitted changes anywhere in the repo, stage and commit them:

```
git add -A
git commit -m "chore(<tenant_id>): snapshot before baseline reset"
```

If the working tree is clean, skip this step.

### Step 2: Delete non-baseline prompt variants

- **Modules layout**: For each directory under `prompts/modules/*/`, run `git rm` on every `variant-{002..NNN}.md` file. Keep `variant-001.md`.
- **Flat layout**: In `prompts/variants/`, run `git rm` on every `variant-{002..NNN}.md` file. Keep `variant-001.md`.

Pattern to match: any file matching `variant-0*.md` where the variant number is > 001. Use glob `variant-0[0-9][2-9].md` or enumerate; the safest approach is to list all `variant-*.md` files and exclude `variant-001.md`.

### Step 3: Delete chain variants

If `chains/variants/` exists and contains files (other than `.gitkeep`):
- `git rm` all files in `chains/variants/` except `.gitkeep`

Do NOT touch files directly in `chains/` (those are baseline chain files).

### Step 4: Clean up configs

Configs are typically gitignored. For each JSON file in `configs/`:
- If it contains `prompt_paths` or `prompt_path` values referencing any variant other than `variant-001`, either:
  - **Rewrite** the path(s) to point to `variant-001` instead, OR
  - **Delete** the config file with `rm` (not `git rm`, since configs are gitignored)
- If a config references only `variant-001`, leave it alone.
- Never delete `.gitkeep`.

For tracked configs (check with `git ls-files configs/`): use `git rm` for deletion or edit + `git add` for rewrites.

### Step 5: Truncate iteration memory

If `docs/iteration-memory.jsonl` exists:
- Truncate it to an empty file (0 bytes). Do NOT delete it — keep the file so the optimization agent has a place to write.
- `git add` the change.

### Step 6: Clean changelog

Read `docs/change-log.md` and process it section by section (sections are delimited by `## ` headers):

1. **Remove** any section where all content references `variant-002` through `variant-NNN`, prompt iteration scores for non-baseline variants, or optimization loop results.
2. **Keep** sections about: baseline setup, tenant scaffold creation, documentation additions, infrastructure changes with no variant references beyond `variant-001`.
3. **Edit** mixed sections: if a section contains both infrastructure/baseline content AND variant-002+ references, remove only the variant-specific bullets/paragraphs while preserving the rest.
4. **Preserve** the file header (title, any preamble before the first `##` section).

After editing, `git add docs/change-log.md`.

### Step 7: Clean local eval outputs

Remove contents of these directories if they exist (these are gitignored, use `rm -rf`):
- `evals/tmp/*`
- `reports/*` (but keep `reports/.gitkeep` if present)

### Step 8: Reset commit

Stage the tenant directory and commit:

```
git add tenants/<tenant_id>/
git commit -m "chore(<tenant_id>): reset to baseline (variant-001)"
```

### Step 9: Summary

Print a summary of what was done:
- Number of prompt variant files removed
- Number of chain variant files removed
- Number of config files cleaned/removed
- Whether iteration memory was truncated
- Number of changelog sections removed/edited
- Whether eval outputs were cleaned

## Safety Rules

**NEVER touch any of these**, regardless of what they contain:
- `variant-001.md` files (baseline prompts)
- Baseline chain files in `chains/` (only touch `chains/variants/`)
- `source_artifacts/` (protected per CLAUDE.md)
- `code/` directory
- `datasets/` directory
- `tests/` directory
- `examples/` directory
- `storage/` directory
- `docker/` directory
- `scripts/` directory
- `.gitkeep` files anywhere
- Any file outside `tenants/<tenant_id>/`

## Edge Cases

- **Tenant already at baseline**: If pre-flight finds nothing to reset, report "Tenant is already at baseline" and stop. Do not create empty commits.
- **Untracked files in prompt/chain directories**: Include them in deletion if they match variant-002+ patterns. Use plain `rm` for untracked files, `git rm` for tracked files.
- **Uncommitted changes outside tenant directory**: The snapshot commit in Step 1 covers the entire repo. This is intentional — it preserves any in-flight work before the reset.
- **No changelog file**: Skip Step 6 if `docs/change-log.md` does not exist.
- **No iteration memory file**: Skip Step 5 if `docs/iteration-memory.jsonl` does not exist.
- **Configs with complex variant references**: Some configs may reference variants in nested structures. Search the full JSON content for patterns like `variant-002`, `variant-003`, etc. When in doubt, delete the config file rather than risk a partial rewrite.
