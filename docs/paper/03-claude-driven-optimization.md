# 3. Claude-Driven Optimization

The optimization loop is the central capability of Hephaestus.
Rather than requiring manual prompt engineering, the system uses Claude Code [CITATION: claudecode] as the orchestration layer: Claude agents drive the optimization process while Claude skills provide reusable building blocks.

## 3.1 Agent and Skill Architecture

The optimization system is composed of Claude Code agents and skills that work together:

**Table 2: Claude Code components in the Hephaestus optimization loop. Agents make decisions; skills execute discrete tasks. The optimization agent composes these automatically.**

| Component | Type | Role |
|-----------|------|------|
| Optimization | Agent | Primary orchestrator. Reads the tenant playbook, produces a scope contract, drives the evaluate--attribute--propose--review loop, and manages level transitions. |
| Step Attribution | Subagent | Post-eval failure analysis. Runs rule-based heuristics followed by LLM-based deep analysis to classify failures as prompt- or structurally-addressable. |
| Variant Reviewer | Subagent | Independent guardrail. Validates proposed variants for scope compliance, placeholder integrity, data leakage, and scorer compatibility. |
| Eval Runner | Skill | Executes an evaluation against a tenant config and returns score summaries. |
| Synthetic Samples | Skill | Generates realistic synthetic test cases for dataset augmentation. |
| Synthetic Pruner | Skill | Validates and cleans synthetic data (placeholder normalization, compliance checks). |
| Reset Tenant | Skill | Resets a tenant to baseline, removing all optimization artifacts. |

The user initiates optimization by invoking the `/optimization` skill in Claude Code with a tenant identifier, config path, and success criteria.
The optimization agent takes over autonomously from there.

## 3.2 The Optimization Loop

The agent's first action is to read the tenant's iteration playbook and produce a **scope contract**: which optimization levels are allowed (prompt text, chain parameters, chain structure) and which are forbidden.
This contract is a hard gate---scope violations are non-negotiable.

The loop then proceeds:

1. **Evaluate**: Invoke the eval-runner skill on the training split, collecting per-case results with step-level outputs.
2. **Attribute**: Dispatch the step-attribution subagent, which runs rule-based heuristics (cascade detection, retrieval quality scoring, format failure detection) followed by LLM-based deep analysis for ambiguous cases. The output partitions failures into *prompt-addressable* and *structural-addressable* counts with confidence levels.
3. **Propose**: The optimization agent generates a new prompt variant targeting the dominant failure cluster, within scope constraints.
4. **Review**: The variant-reviewer subagent independently validates the proposal against guardrails: scope compliance, placeholder preservation, example leakage, and scorer compatibility. A `fail` verdict triggers revision; persistent failures are escalated to the user.
5. **Re-evaluate and compare**: Run the new variant and compare against the previous best.
6. **Iterate or escalate**: Accept variants with measurable improvement. When performance plateaus at one level (after exhausting a strategy ladder of module isolation, technique diversity, web research, and ablation), record exhaustion in iteration memory and escalate to the next allowed level.

The system operates at three granularity levels---prompt text, chain parameters (e.g., retrieval depth, temperature), and chain structure (adding or removing nodes)---and exhausts one level before escalating to the next.

## 3.3 Guardrails and Data Hygiene

Automated optimization introduces overfitting risk.
Hephaestus mitigates this through:

- **Split access controls**: The optimizer inspects individual cases only from the training split. Validation and test splits expose only aggregate scores.
- **Scope constraints**: Tenant playbooks define allowed and forbidden optimization levels. Both the optimization agent and the variant reviewer enforce these independently.
- **Iteration memory**: A structured log (`iteration-memory.jsonl`) records each cycle---variants tried, scores achieved, exhaustion reasons---preventing rework and providing an audit trail.
- **Variant immutability**: Every iteration creates a new variant file. No in-place editing ensures full rollback capability.
