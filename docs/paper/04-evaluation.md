# 4. Evaluation

We evaluate Hephaestus on two tasks: a multi-hop QA benchmark (HotpotQA) and a security-domain classification task (CTIBench Root Cause Mapping).
In both cases we replicate published experimental setups as Hephaestus tenants, then run the Claude optimization agent with prompt-only scope constraints.

## 4.1 Tasks

### HotpotQA multi-hop QA

We replicate the GEPA pipeline [CITATION: gepa] as a six-node LangGraph chain: two BM25 retrieval nodes (k = 7) and four LLM nodes (GPT-4.1-mini, temperature 1.0).
The scorer computes exact match (EM) and token-level F1, matching GEPA's protocol.
Dataset splits follow GEPA: 150 dev / 300 val / 300 test from the fullwiki setting.
Baseline prompts (variant-001) use minimal DSPy-style instructions.

### CTIBench Root Cause Mapping (RCM)

CTIBench-RCM [CITATION: ctibench] maps CVE descriptions to CWE IDs---a 263-class classification task following NVD conventions.
We replicate the experimental setup from the Foundation-Sec paper [CITATION: foundationsec]: single-node classification chain, exact-match scoring on extracted CWE IDs.
The 1000-case dataset is split into 173 dev (stratified by CWE) and 827 test, with rare CWEs ($\leq$3 cases) appearing only in test to prevent overfitting.
We optimize across three models: GPT-5, Foundation-Sec-8B-Instruct, and Foundation-Sec-8B-Reasoning.

## 4.2 Results

### HotpotQA

Table 3 below shows the optimization progression.
The attribution subagent identified three failure categories on the dev set: near-miss (verbose answers, 13 cases), gave-up (model declined to answer, 8 cases), and wrong-answer (17 cases).
Variant-002 addressed near-miss failures with answer brevity constraints (+26.34pp val EM); variant-003 addressed gave-up failures with a must-always-answer rule (+4.66pp).
After two iterations the attribution system flagged remaining failures as retrieval-limited (structural), signaling the agent to stop prompt-level iteration.

**Table 3: HotpotQA optimization (GPT-4.1-mini, BM25 k = 7, temp 1.0). Test averaged over 3 runs. Two automated iterations yield +31pp improvement on heldout set.**

| Variant | EM (dev) | F1 (dev) | EM (val) | F1 (val) | EM (test) |
|---------|----------|----------|----------|----------|-----------|
| variant-001 (baseline) | 40.67 | 51.73 | 39.33 | 53.28 | 34.67 |
| variant-002 | 74.67 | 80.21 | 65.67 | 72.98 | --- |
| variant-003 (best) | 80.00 | 84.66 | 70.33 | 77.48 | 72.67 |

### CTIBench-RCM

Table 4 below shows results across three models.
Each model was optimized independently by the same Claude optimization agent with a 25-variant budget and prompt-only scope.
Total variants tested: 88 across the three models.

The agent discovered qualitatively different optimal strategies per model.
GPT-5 benefited from surgical NVD convention rules targeting specific CWE confusion pairs (e.g., buffer overflows $\rightarrow$ CWE-787, not CWE-121/122), improving from 71.1% to 76.1% test accuracy across 31 variants.
Foundation-Sec-8B-Instruct, by contrast, required the *opposite* approach: any added rules or structure destroyed format extraction; the best prompt was an ultra-concise instruction mentioning "NVD mapping conventions" with no specific rules (30 variants, +2.3pp test).
Foundation-Sec-8B-Reasoning achieved its best result with a single key phrase---"standard NVD abstraction level"---which activated domain-specific training knowledge; 27 variants confirmed this as a sharp optimum, with ablation showing the phrase alone accounts for +2.9pp dev improvement.

Across all three models, the remaining failures are dominated by label noise in the benchmark (CWE-787 vs. CWE-121/122 ambiguity in buffer overflow descriptions) and genuinely ambiguous singletons---consistent with an estimated accuracy ceiling of 85--88% on this dataset.

**Table 4: CTIBench-RCM optimization. All scores are exact-match accuracy (%). Prompt-only, 25-variant budget per model.**

| Model | Variants | Dev (base) | Dev (best) | Test (base) | Test (best) |
|-------|----------|------------|------------|-------------|-------------|
| GPT-5 | 31 | 78.6 | 85.6 | 72.1 | **76.1** |
| Foundation-Sec-8B-Inst. | 30 | 76.3 | 80.4 | 63.9 | **71.0** |
| Foundation-Sec-8B-Reas. | 27 | 80.4 | 83.2 | 71.0 | **73.0** |
