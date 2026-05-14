# 6. Conclusion

We presented Hephaestus, a framework for evaluating and optimizing multi-step LLM pipelines.
Its core contributions are a domain-agnostic evaluation engine with pipeline-aware scoring, a multi-tenant isolation model, and a Claude-driven optimization loop that uses step-level failure attribution to guide targeted prompt improvements within explicitly scoped guardrails.
On HotpotQA, two automated iterations improved exact-match from 39.3% to 70.3% (+31pp), with the attribution system correctly distinguishing prompt-addressable failures from structural retrieval limitations.
On CTIBench-RCM, the agent autonomously discovered model-specific strategies---surgical classification rules for GPT-5, minimal prompts for Foundation-Sec-8B-Instruct---across 88 variants and three models, matching or exceeding published baselines.
The framework is generic by design: the same infrastructure drives multi-hop QA and security-domain classification.
We believe the combination of Claude Code orchestration with structured evaluation provides a practical path toward systematic, reproducible prompt engineering for complex LLM applications.

[REFERENCES: bibliography placeholder]
