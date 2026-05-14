# 2. System Overview

## 2.1 Architecture

Hephaestus has two layers.
The **core engine** (`src/hephaestus/`) is domain-agnostic: it provides dataset loading, prompt template rendering, LLM provider abstraction, LangGraph chain execution, scoring validation, and eval run management.
The **tenant layer** (`tenants/<id>/`) contains everything task-specific: LangGraph chain definitions, prompt templates with versioned variants, scorer implementations, datasets, eval configurations, and structured documentation.

The key design principle is that everything in the core engine is generic.
A tenant for multi-hop question answering uses the same evaluation infrastructure as a tenant for security incident summarization---only the chain topology, prompts, scorer logic, and datasets differ.

An evaluation run proceeds as:

1. Load a JSON config specifying the tenant, LLM provider, dataset, chain, and scoring profile.
2. Construct a provider client (OpenAI, Baseten, or SageMaker) and dynamically import the tenant's chain factory to build a compiled `StateGraph`.
3. For each case, invoke the chain, extract the final output and all intermediate step outputs from the chain state.
4. Score using the tenant's scorer, which returns a composite score (0--100) and a named score breakdown.

Cases execute concurrently via a thread pool with real-time progress tracking.
Results are persisted as structured JSONL alongside the run configuration for reproducibility.

## 2.2 Chains and Pipeline-Aware Scoring

Evaluation targets are LangGraph `StateGraph` objects compiled into executable chains.
Every chain operates on a state dictionary conforming to the `ChainState` protocol (see Table 1 below).

**Table 1: The `ChainState` protocol. Tenant chains may extend this with additional fields.**

| Field | Type | Description |
|-------|------|-------------|
| `context` | `Dict[str, str]` | Input from the evaluation case |
| `output_text` | `str` | Final chain output for scoring |
| `step_outputs` | `Dict[str, str]` | Intermediate outputs, keyed by node name |
| `diagnostics` | `List[str]` | Debug traces and warnings |

The framework provides a `make_llm_node` factory that constructs chain nodes from prompt template files.
At invocation, each node merges the case context with prior step outputs (referenced as `${steps.<name>.output}` in templates), calls the provider, optionally parses the output, and writes results into `step_outputs` for downstream nodes.

Tenant scorers implement a `Scorer` interface with two entry points: `score_case` (final output only) and `score_pipeline_case` (all intermediate step outputs).
Every score payload includes a **composite_score** in $[0, 100]$ and a **score_breakdown** dictionary of named sub-scores (e.g., `exact_match`, `f1`, `format_compliance`).
Pipeline-aware scoring is what enables the attribution system (see Section 3) to distinguish failures caused by upstream steps from those caused by final generation.

## 2.3 Tenant Isolation

Each tenant is a self-contained directory: prompt variants organized by module and version (`variant-NNN.md`), dataset splits in JSONL, chain definitions, scorer code, and a documentation contract (tenant profile, data contract, prompt contract, eval operations guide, and an iteration playbook defining optimization scope and success criteria).

This isolation enables concurrent optimization of unrelated tasks without interference and enforces data sensitivity boundaries.
Prompt variants are never edited in place; each iteration creates a new numbered variant, preserving full history and enabling rollback.
