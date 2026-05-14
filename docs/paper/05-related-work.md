# 5. Related Work

## Prompt optimization

GEPA [CITATION: gepa] uses evolutionary search (genetic operators) to optimize prompts for multi-step reasoning pipelines.
Hephaestus generalizes GEPA's evaluation infrastructure into a reusable multi-tenant framework and replaces evolutionary search with attribution-driven optimization orchestrated by Claude Code agents.
DSPy [CITATION: dspy] compiles declarative LLM programs into optimized pipelines; MIPRO [CITATION: mipro] extends DSPy with joint optimization of instructions and demonstrations for multi-stage programs.
APE [CITATION: ape] frames instruction generation as black-box optimization, using an LLM to propose and score candidate prompts.
OPRO [CITATION: opro] embeds an "optimization trajectory" of past candidates and scores directly in the prompt, using the LLM itself as the optimizer.
EvoPrompt [CITATION: evoprompt] and PromptBreeder [CITATION: promptbreeder] apply evolutionary algorithms---with LLM-assisted mutation operators---to maintain populations of candidate prompts.
TextGrad [CITATION: textgrad] treats textual feedback as a gradient-like signal over a computation graph of LLM calls, optimizing prompts as differentiable variables.
None of these systems combine pipeline-aware step-level attribution with scope-constrained guardrails and multi-tenant isolation.

## From jailbreaking to prompt optimization

Prompt optimization and jailbreaking are best understood as two objective functions over the same control surface: search over discrete prompt space guided by an evaluation signal.
The lineage begins with universal adversarial triggers [CITATION: triggers], which used gradient-guided token search to find input-agnostic sequences that transfer across examples and models.
AutoPrompt [CITATION: autoprompt] applied the same gradient-guided discrete search to *improve task performance*.
GCG [CITATION: gcg] then adapted token-level optimization to aligned chat models, producing universal adversarial suffixes that transfer to black-box targets---and explicitly framing the method as "automated prompt generation."
At the semantic level, PAIR [CITATION: pair] used an attacker LLM to iteratively refine jailbreak prompts with only black-box access;
TAP [CITATION: tap] scaled this into a tree search with pruning, reporting high success rates on frontier models with reduced query budgets.
AutoDAN [CITATION: autodan] applied genetic algorithms with a stealthiness constraint---isomorphic to constraint satisfaction in benign prompt optimization.
Recent systems make the dual-use connection explicit:
EvoX [CITATION: evox] meta-evolves both candidate prompts and the search strategies that generate them;
AdaEvolve [CITATION: adaevolve] adds hierarchical adaptive scheduling to LLM-driven evolutionary search;
Claudini [CITATION: claudini] uses Claude Code agents to iteratively discover white-box adversarial attacks that recombine GCG variants---the same evaluate--analyze--propose--iterate loop that Hephaestus applies to constructive pipeline improvement.
Hephaestus differs from these systems in its focus on multi-step pipeline attribution, scope-constrained guardrails, and multi-tenant isolation rather than single-objective search.

## Jailbreak benchmarks and scaling

Standardized evaluation has become critical as jailbreak methods proliferate.
HarmBench [CITATION: harmbench] provides a framework for systematic comparison of red-teaming attacks and defenses, including adversarial training baselines.
JailbreakBench [CITATION: jailbreakbench] adds an evolving repository of "jailbreak artifacts," standardized threat models, and reproducible scoring---motivated by incomparable success-rate and cost reporting across prior work.
Empirical studies of in-the-wild jailbreak prompts [CITATION: danjailbreak] document community-driven prompt optimization over months, with effective prompts persisting and evolving for stealthiness---mirroring the iterative refinement loops formalized in constructive optimizers.
On the scaling side, [CITATION: capscaling] formalize capability-based scaling trends showing that attacker--target capability gaps predict jailbreaking success, motivating automated over manual red-teaming.
[CITATION: advreasoning] frame jailbreaking as a test-time compute optimization problem, connecting adversarial prompt search to the broader inference-time scaling paradigm.

## Prompt injection in agentic systems

When LLM pipelines process untrusted content---retrieved documents, browsing results, tool outputs---prompt injection becomes a first-class security risk.
Indirect prompt injection [CITATION: indirectinjection] demonstrated that instructions embedded in retrieved data can hijack model behavior even when not human-visible, blurring the boundary between data and instructions.
Industry guidance now treats this as a primary application security concern: OpenAI [CITATION: openai_injection] publishes agent-focused mitigations emphasizing constrained tool actions and workflow design; OWASP [CITATION: owasp_llm] ranks prompt injection as the top LLM application risk.
The same pipeline-aware architecture that enables Hephaestus's optimization---where multiple context sources feed into chained LLM calls---also defines the attack surface for injection.
Hephaestus's tenant isolation and scope constraints provide partial mitigation by limiting what the optimization loop can modify, but end-to-end defenses for agentic prompt injection remain an open problem.

## LLM evaluation

HELM [CITATION: helm] and BIG-bench [CITATION: bigbench] benchmark model capabilities across diverse tasks but focus on model selection rather than iterative prompt improvement.
AgentBench [CITATION: agentbench] and SWE-bench [CITATION: swebench] evaluate agent capabilities in interactive environments.
MT-Bench [CITATION: mtbench] uses LLM-as-a-judge for multi-turn evaluation; PromptBench [CITATION: promptbench] tests prompt robustness under adversarial perturbations.
None provide the combination of pipeline-aware scoring, step-level attribution, and closed-loop optimization.

## Agentic frameworks

ReAct [CITATION: react] interleaves reasoning and tool use in a single-agent loop.
LangGraph [CITATION: langgraph] provides the stateful graph execution that Hephaestus builds on for chain definition.
Claude Code [CITATION: claudecode] provides the agent and skill infrastructure that Hephaestus uses as its optimization orchestration layer, enabling autonomous multi-step workflows with tool use, subagent dispatch, and persistent context.
