# Hephaestus: Claude-Driven Optimization of Multi-Step LLM Pipelines

**Authors:** Paul Kassianik, Blaine Nelson, Supriti Vijay, Aman Priyanshu, Baturay Saglam, Amin Karbasi

**Affiliation:** Foundation AI -- Cisco Systems Inc.

**Corresponding author:** paulkass@cisco.com

## Abstract

Multi-step LLM pipelines---chains of retrieval, summarization, reasoning, and formatting calls---are increasingly used for complex tasks in security, enterprise analytics, and knowledge work.
Optimizing these pipelines remains largely manual: practitioners edit prompts by intuition, evaluate on ad-hoc examples, and lack tools for diagnosing which step in a chain causes a failure.
We present **Hephaestus**, a Claude Code-based framework for optimizing LLM chains.
Hephaestus provides a multi-tenant isolation model, pipeline-aware scoring, and a closed-loop optimization system orchestrated by Claude Code agents and skills.
The optimization loop uses Claude to analyze step-level failures, propose scoped prompt variants, validate them through an independent reviewer agent, and iterate---all within explicitly defined guardrails.
We evaluate on two tasks: HotpotQA multi-hop QA, where we replicate the GEPA baseline and improve exact-match from 39.3% to 70.3% (+31pp) in two iterations; and CTIBench Root Cause Mapping, a security-domain CVE-to-CWE classification task, where prompt-only optimization across three models (GPT-5, Foundation-Sec-8B-Instruct, Foundation-Sec-8B-Reasoning) matches or exceeds published baselines.
