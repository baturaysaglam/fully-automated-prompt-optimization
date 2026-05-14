# Appendix

## A. Optimization Loop Diagram

The following diagram (from the Hephaestus README) shows the closed-loop optimization workflow driven by Claude Code agents:

[FIGURE: hephaestus_optimization_loop.pdf — The Hephaestus optimization loop. Claude agents (purple) analyze failures and propose variants; the variant-reviewer (orange) enforces guardrails; the eval-runner skill (teal) scores each iteration. The loop terminates when the target score is met or the current optimization level is exhausted.]

## B. Optimized Prompt Variants

A key finding is that optimal prompts differ qualitatively across models---even for the same task.
Below we show the baseline and best-performing CTIBench-RCM prompts for each model, and the HotpotQA answer-generation prompts before and after optimization.

### B.1 CTIBench-RCM: Baseline (variant-001, all models)

```
System: You are a cybersecurity expert specializing in
vulnerability analysis and weakness classification.

Analyze the following CVE description and map it to the
appropriate CWE. Provide a brief justification for your
choice. Ensure the last line of your response contains
only the CWE ID.

User: ${description}
```

### B.2 CTIBench-RCM: GPT-5 Best (variant-029, 76.1% test)

The optimization agent discovered that GPT-5 benefits from *surgical NVD convention rules* targeting specific CWE confusion pairs.
The prompt grew from 4 lines to 23, with each rule addressing a measured failure cluster:

```
System: You are a cybersecurity expert specializing in
vulnerability analysis and weakness classification.

Analyze the following CVE description and map it to the
appropriate CWE. Provide a brief justification for your
choice. Ensure the last line of your response contains
only the CWE ID.

When selecting a CWE, follow NVD mapping conventions:
- Buffer overflows (stack/heap/unspecified) -> CWE-787,
  not CWE-121 or CWE-122.
- Command injection -> CWE-77, not CWE-78, unless the
  description explicitly describes OS-level commands.
- Hardcoded credentials -> CWE-798.
- DoS through malformed input -> CWE-404 when there is
  no indication of memory corruption.
- Weak crypto -> CWE-327.  Missing authz -> CWE-862.
- Integer overflow -> CWE-190.  NULL deref -> CWE-476.
- Use-after-free -> CWE-416.
- Observable timing/side-channel -> CWE-203.
- Info exposure through error messages -> CWE-209.

Common mistakes to avoid:
- Do NOT use CWE-20 as a catch-all.
- Focus on root cause, not impact or attack vector.

User: ${description}
```

### B.3 CTIBench-RCM: Foundation-Sec-8B-Instruct Best (variant-037, 71.0% test)

For the Instruct model, the optimization agent discovered the *opposite* strategy: any added rules destroyed format extraction.
The optimal prompt is two lines---a 5x reduction from baseline:

```
System: You are a CWE classification expert following NVD
mapping conventions. Given a CVE description, identify the
root cause CWE. Output the CWE ID on the last line.

User: ${description}
```

### B.4 CTIBench-RCM: Foundation-Sec-8B-Reasoning Best (variant-072, 73.0% test)

The Reasoning model's best prompt is nearly identical to the Instruct prompt, except for one critical phrase---"standard NVD abstraction level"---which ablation showed accounts for +2.9pp:

```
System: You are a CWE classification expert. Map the CVE
description to the most appropriate CWE following NVD
mapping conventions. Use the standard NVD abstraction
level. Output the CWE ID on the last line.

User: ${description}
```

### B.5 HotpotQA: Answer Generation Before and After

The HotpotQA baseline uses a bare DSPy-format prompt with no task-specific instructions.
The optimized variant-003 adds answer brevity rules, a must-always-answer constraint, and format guidance---changes identified by the attribution subagent analyzing near-miss and gave-up failures.

#### Baseline (variant-001, 39.3% val EM)

```
System: Your input fields are:
1. `question` (str):
2. `summary_1` (str):
3. `summary_2` (str):
Your output fields are:
1. `reasoning` (str):
2. `answer` (str):
[...]
In adhering to this structure, your objective is:
  Given the fields `question`, `summary_1`, `summary_2`,
  produce the fields `answer`.
```

#### Optimized (variant-003, 70.3% val EM)

```
System: You answer multi-hop questions with the SHORTEST
possible answer.

CRITICAL RULES:
1. MUST ALWAYS provide an answer. NEVER say "unknown",
   "none", "N/A", or "not enough information".
2. If summaries contain partial info, use what you have
   to make your best inference.
3. If the question asks for a comparison and you only
   have data for one entity, answer with that entity.

ANSWER FORMAT RULES (follow EXACTLY):
- Output ONLY the entity name, number, date, or yes/no.
- NEVER output a full sentence as the answer.
- For yes/no questions: "yes" or "no" (lowercase).
- For "who": just the full name (e.g., "James Cameron").
- For "when": just the date (e.g., "1066").
- Copy names EXACTLY as spelled in the summaries.
- Use SINGULAR form when the question asks "what".
```

## C. CTIBench-RCM Full Variant Progression

Table C.1 below shows the full GPT-5 variant progression on the dev set, illustrating how the optimization agent explored the strategy space.
The agent tested 31 variants, with scores ranging from 76.3% to 85.6%.
Early variants (002--004) tried broad abstraction rules and regressed; variant-005 introduced surgical NVD rules for specific CWE confusion pairs and jumped +4pp.
Subsequent variants refined the rule set, with diminishing returns past variant-026.

**Table C.1: GPT-5 variant progression on CTIBench-RCM dev set (173 cases). Selected variants shown; full history in the tenant change log.**

| Var. | Strategy | Dev EM |
|------|----------|--------|
| 001 | Baseline (simple classify prompt) | 78.6 |
| 002 | Prefer parent CWE + examples | 76.3 |
| 005 | Surgical NVD rules (787, 77, 404, 798) | 82.7 |
| 012 | CWE-787 + CWE-798 only | 80.9 |
| 020 | + CWE-327/862 rules | 83.2 |
| 022 | + CWE-190/476/416 rules | 83.8 |
| 026 | + negative examples + CWE-203/209 | 84.4 |
| 029 | Refined CWE-404 wording | **85.6** |
| 031 | + CWE-287/401 rules (regressed) | 83.8 |
