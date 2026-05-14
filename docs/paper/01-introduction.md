# 1. Introduction

Multi-step LLM pipelines---chains of retrieval, summarization, reasoning, and formatting calls---are increasingly used for complex tasks in security, enterprise analytics, and knowledge work.
Unlike single-turn prompting, these systems compose several dependent model calls, so failures in the final output may originate in earlier intermediate steps.
Despite their growing importance, optimizing such pipelines remains largely manual: practitioners edit prompts by intuition, evaluate on ad-hoc examples, and often lack tools to diagnose which step in a chain caused a failure.

Existing frameworks do not fully address this setting.
Model evaluation suites such as HELM [CITATION: helm], BIG-bench, and AgentBench benchmark capabilities but do not support iterative prompt optimization for a fixed pipeline.
Prompt-programming systems such as DSPy [CITATION: dspy] optimize individual modules, but do not natively provide multi-tenant isolation, pipeline-aware diagnostics, or explicit guardrails against overfitting during automated iteration.
In practice, improving a multi-step chain is still a slow, unstructured process of prompt tweaking, partial evaluation, and guesswork about where errors originate.

We present **Hephaestus**, a Claude Code-based framework for evaluating and optimizing multi-step LLM pipelines.
Hephaestus combines four core ideas.
First, it uses a **two-layer architecture** that separates a reusable evaluation engine from isolated tenant environments, each with its own chains, prompts, datasets, scorers, and documentation contracts.
Second, it provides **pipeline-aware evaluation** through LangGraph [CITATION: langgraph] chains and a standardized `ChainState` protocol, enabling scorers and analysis tools to inspect intermediate step outputs rather than only final answers.
Third, it introduces a **Claude-driven optimization loop** in which Claude Code agents analyze step-level failures, propose scoped prompt variants, validate them through an independent reviewer agent, run evaluations, and iterate within explicitly defined guardrails.
Fourth, it enforces **guardrails and data hygiene** through tenant-defined scope constraints, split-aware access controls, and iteration memory that reduce overfitting and repeated work during automated optimization.

We evaluate Hephaestus on two tasks.
On HotpotQA [CITATION: hotpotqa], we replicate the GEPA baseline [CITATION: gepa] and improve exact match from **39.3% to 70.3% (+31pp)** in two automated iterations.
On CTIBench Root Cause Mapping [CITATION: ctibench], a security-domain CVE-to-CWE classification task, prompt-only optimization across three models (GPT-5, Foundation-Sec-8B-Instruct, and Foundation-Sec-8B-Reasoning [CITATION: foundationsec]) matches or exceeds published baselines.
These results show that structured, attribution-driven optimization can substantially improve multi-step LLM systems without changing the underlying model or task formulation.

At Foundation AI, we use the same approach to optimize security pipelines in production-oriented settings.
More broadly, Hephaestus is designed as a generic framework: the same evaluation and optimization infrastructure can support tasks as different as multi-hop question answering, vulnerability classification, and other chained LLM workflows.
