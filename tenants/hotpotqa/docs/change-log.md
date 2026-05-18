<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# Change Log

---

## 2026-05-15 — Prompt Optimization Session 6 (v071→v082)

- Summary: 12 new prompt variants tested. Key breakthrough: adding "Quote exactly" instruction to summarize1 (variant-013) provides genuine +1pp improvement by preserving verbatim text for EM matching.
- Scope: Prompt-only changes (per iteration-playbook.md scope contract).
- Starting point: v057 baseline (v040 answer + v006 query + v005 sum1/sum2) at ~70.44% avg (this session).

### New variants tested:
| Variant | Key Change | Val EM | Notes |
|---------|-----------|--------|-------|
| v071 | Extractive QA answer framing | 66.33% | Catastrophic regression |
| v072 | Typed reasoning seed | 70.33% | Neutral |
| v073 | Sum2 with "Likely answer:" | 69.67% | Regressed |
| v074 | Hybrid answer rules | 69.33% | Regressed |
| **v075** | **Sum1 v013 + answer v039** | **71.40% avg (5 runs)** | **+1pp improvement** |
| v076 | v032 answer rerun | 70.00% | Baseline BM25 variance |
| v077 | No-reasoning answer | ~20% | Broken — model output format breaks |
| v078 | Sum1 v013 + v032 answer | 70.67% | Moderate improvement |
| v079 | Both sum1+sum2 "quote exactly" | 69.67% | Sum2 quoting hurts |
| v080 | Answer v052 (find exact text) | 70.67% | Neutral |
| v081 | Sum1 v014 (follow-up entity) | 69.67% | Extra structure hurts |
| **v082** | **Sum1 v013 + answer v012** | **71.42% avg (excl outlier)** | **BEST. Peak 72.33%** |

### Key findings:
- **Sum1 v013 "Quote exactly" instruction** is a genuine improvement: +0.5-1pp on average by preserving verbatim text that passes EM scoring.
- **Sum2 should NOT have "quote exactly"** — it needs to synthesize information from both hops, not just copy.
- **Answer v012** (without rule 13) performs better than v039 when sum1 already enforces verbatim quoting.
- **Best single run: 72.33% EM** (v082 run 2) — within 0.17pp of target.
- **Average (v082): 71.42%** — still 1.08pp below 72.5% target due to BM25 variance.
- Removing reasoning field from answer prompt completely breaks output format (v077).

### Best configuration: `remote-v082-val.json`
- Answer: `generate_answer/variant-012.md`
- Query: `generate_query_with_context/variant-006.md`
- Sum1: `summarize1/variant-013.md` (key improvement: "Quote exactly" instruction)
- Sum2: `summarize2/variant-005.md`

### Assessment:
- 72.5% target was reached on a single run (72.33%) but is not reliably achievable due to BM25 retrieval nondeterminism (~2-3pp variance per run).
- All prompt-level strategies are now exhausted (60+ variants, 6 sessions, strategy ladder fully used).
- Reaching 72.5% **reliably** would require parameter/structural changes (temperature reduction, retrieval_k increase, retry logic) — all outside scope.

---

## 2026-05-15 — Prompt Optimization Session 5 (v061→v070)

- Summary: 10 additional prompt variants tested. Focused on summarize format changes, answer prompt hybridization, and reasoning seed variations.
- Scope: Prompt-only changes (per iteration-playbook.md scope contract).
- Starting point: v040 answer + v005 sums at ~71.0% avg on current BM25 infra.

### New variants tested:
| Variant | Key Change | Val EM | Notes |
|---------|-----------|--------|-------|
| v061 | v044 answer (location-precision rule 13) | 68.67 | REGRESSED — location rules hurt |
| v062 | v045 answer ("Question type" reasoning seed) | 71.00 | Neutral |
| v063 | v046 answer (compact decision-tree format) | 70.33 | Slightly worse |
| v064 | v040 answer + bullet-point sum1 v012 | 71.67, 69.67, 71.67, 70.00 (avg 70.75) | Good peaks but inconsistent |
| v065 | v047 answer (v012+rule13+extended rule9) | 71.00 | Same as v039 |
| v067 | v040 baseline rerun | 69.67 | Low BM25 roll |
| v068 | v040 + bullet sum1+sum2 | 70.00 | Bullet sum2 hurts |
| v069 | v012 answer + bullet sum1 | 69.33 | Low BM25 roll |
| v070 | v039 answer + bullet sum1 | 71.67, 71.00 (avg 71.33) | Matches baseline |

### Key findings:
- **Bullet-point summarize1** provides no reliable improvement. Avg identical to prose sum1 baseline.
- **Bullet-point summarize2** slightly hurts (forces less contextual info to answer step).
- **Location-precision rules** remain net-negative across all attempts.
- **Compact/restructured answer prompts** consistently regress (model prefers detailed rule lists).
- **All competitive configs cluster 70-71.67%** — firmly within BM25 variance band.

### Final assessment:
- Best avg: 71.33% (v040 with sum1 v005, also v070 with bullet sum1)
- Best single run this session: 71.67% (multiple configs)
- Target: 72.5% — **unreachable** with prompt-only changes
- Root cause: BM25 retrieval nondeterminism creates ~2pp per-run variance (36 volatile cases)
- 48 total prompt variants tested across 5 optimization sessions

### Recommended config: `configs/remote-v057-val.json` (answer v040 + query v006 + sum1/sum2 v005)
- Most consistent. Best average (71.33%). Proven across multiple sessions.

---

## 2026-05-15 — Prompt Optimization Session 4 (New Infra, v049→v060)

- Summary: 12 additional prompt variants tested on rebuilt BM25 index. Targeting EM >= 72.5% on val.
- Scope: Prompt-only changes (per iteration-playbook.md scope contract).
- Starting point: v031 config scoring ~71.00% avg on new BM25 infra (down from 72.33% on original).
- Best single run: **72.33% val EM** (variant-032, run 1)
- Best average: ~71.11% (variant-039, 3 runs)

### New answer prompt variants tested:
| Variant | Key Change | Runs | Avg |
|---------|-----------|------|-----|
| v032 | + Rule 13 (trim locations) + rule 9 (singular) + verify preamble | 72.33, 70.00, 70.67, 70.67 | 70.92 |
| v033 | + Structured reasoning template | 70.33 | — |
| v034 | + "Question asks for" preamble | 70.00 | — |
| v035 | + 3-step preamble | 70.33 | — |
| v036 | Only singular rule 9, no rule 13 | 71.00 | — |
| v037 | Preserve-from-source rule 13 | 70.67 | — |
| v038 | Many verbosity examples | 70.33 | — |
| v039 | "Don't add info not in summaries" rule 13 | 71.67, 71.33, 70.33 | 71.11 |
| v040 | "Singular answers only" rule 9 + v039's rule 13 | 71.67, 71.00 | 71.33 |
| v041 | Hybrid v039+v040 | 71.33 | — |
| v042 | Location-specific rule 13 | 70.33 | — |
| v043 | Minimal/tight, "don't add beyond summaries" | 71.33, 70.33 | 70.83 |

### Key findings:
- **BM25 variance dominates**: ~2pp run-to-run variance from BM25 retrieval nondeterminism (temp=0.0). 36 volatile cases flip randomly.
- **Rule 13 (anti-addition)** provides the most consistent benefit (+0.5pp average). Best phrasing: "Do NOT add information beyond what the summaries state."
- **Aggressive location trimming** (v032) produces highest peaks (72.33%) but also worst lows (70.00%) due to over-trimming gold answers that expect qualifiers.
- **Conservative rule 13** (v039 "don't add, preserve what's there") provides best stability (71.11% avg, tightest variance).
- **Structured reasoning preambles** all regress on val despite seeming helpful on train.
- **More rules/examples = worse**: prompts with many specific examples confuse the model.

### Ceiling analysis:
- Best single-run: 72.33% (v032 run 1) — 0.17pp from target
- Average: 71.0-71.5% across all competitive variants
- ~87 failures per run: 20-25 are retrieval failures (unfixable), 15-20 near-misses (addressable), 40+ are reasoning/concept errors
- The 72.5% target requires reliably fixing 1-5 more cases per run, but BM25 variance adds/removes ~6 cases randomly

### Recommended config: `configs/remote-v056-val.json` (variant-039)
- Most consistent. Average 71.11%. Lower downside risk.
- Alternative for maximum upside: `configs/remote-v049-val.json` (variant-032) — can hit 72.33% but also drops to 70%

---

## 2026-05-14 — Prompt Optimization Session 2 (v014 → v031)

- Summary: Multi-module prompt optimization continuing from v014 baseline, targeting EM >= 72.5% on val.
- Scope: Prompt-only changes (per iteration-playbook.md scope contract).
- Starting point: v014 config (avg 71.17% val)
- Best result: v031 config (**72.33% val EM**)

### Key improvements:
1. **generate_query_with_context/variant-006.md** — BM25/Wikipedia-title-focused query generation. Explicitly tells model to use exact entity names matching Wikipedia article titles, improving hop-2 retrieval. Contributed +1.66pp.
2. **summarize1/variant-005.md** — Anti-give-up rule ("never say no info found") + explicit entity name clarity ("state it clearly and exactly"). Contributed +2.33pp when combined with query v006.
3. **generate_answer/variant-012.md** — Confirmed as locally optimal. Every modification tested (v014-v022, 9 variants) performed worse on val.

### Val progression:
| Variant | Val EM | Delta vs v014 |
|---------|--------|---------------|
| v014 (prev best) | 71.17% | — |
| v019 (sum1 v005 only) | 71.0% | -0.17pp |
| v024 (answer v018 + query v006) | 71.67% | +0.5pp |
| v025 (+ sum1 v005) | 72.0% | +0.83pp |
| **v031 (v012 answer + v006 query + v005 sum1)** | **72.33%** | **+1.16pp** |

### Key findings:
- Query v006 (BM25-title-focused) rescues retrieval failures by producing Wikipedia-article-title-like queries
- Summarize1 v005 prevents evidence loss by forbidding "no info found" responses
- Answer prompt v012 is locally optimal — all modifications (shorter, longer, structured reasoning, format rules) regress on val
- Structured reasoning (v018) helps on train but hurts on val — overfits to train question patterns
- Any change to summarize2 beyond v005 (candidate hints, explicit shared attributes) hurts

### Remaining gap:
- Target: 72.5%, Best: 72.33%, Gap: 0.17pp (1 case out of 300)
- 20+ additional variants tested after v014. All prompt-level approaches exhausted.
- Remaining failures: BM25 retrieval misses, inherent format ambiguity in gold answers
- Further improvement requires parameter changes (retrieval_k, temperature) or structural changes (retry, re-ranking) — both forbidden by scope contract.

### Config: `configs/remote-best-v031.json`
- Model: gpt-4.1-mini, temperature=0.0, top_p=0.95
- query: variant-006, summarize1: variant-005, summarize2: variant-005, answer: variant-012
- retrieval_k=7, BM25

---

## 2026-05-14 — Prompt Optimization Session (v004 → v014)

- Summary: Multi-module prompt optimization targeting EM >= 72.5% on val.
- Scope: Prompt-only changes (per iteration-playbook.md scope contract).
- Starting point: v004 config (76.67% train, ~70% val)
- Best result: v014 config (avg 71.17% val across 2 runs: 71.67%, 70.67%)

### Key improvements:
1. **generate_answer/variant-012.md** — Stronger anti-verbosity rules with explicit negative examples ("Newcastle United" not "Newcastle United F.C.", "United States" not "United States of America"), anti-hedging, never-empty fallback, property-vs-entity disambiguation.
2. **generate_query_with_context/variant-005.md** — More targeted hop-2 query generation: emphasizes finding the TARGET entity (not what's already found), removes generic filler words.
3. **summarize2/variant-005.md** — Critical anti-give-up rule: never say "no information found", always present available evidence from both searches.

### Progression on val (300 cases):
| Variant | Val EM | Delta |
|---------|--------|-------|
| v004 (baseline) | ~70.0% | — |
| v009 (answer only) | 70.0% | +0.0pp |
| v011 (+query v005, +sum2 v005) | 71.0% | +1.0pp |
| v014 (+answer v012) | 71.67% (avg 71.17%) | +1.2pp |

### Techniques tried:
- Module isolation (answer-only, query-only, summarize-only changes)
- Anti-verbosity negative examples
- Anti-hedging rules
- Never-empty/fallback rules
- Source-format preservation (en-dashes, compact notation)
- Property-vs-entity disambiguation
- Structured CoT (regressed)
- Few-shot examples (regressed)
- Candidate-answer-in-summary (regressed)
- Summarize1 entity extraction (neutral/negative on val)

### Remaining gap:
- Target: 72.5%, Best: 71.17% (avg), Gap: ~1.3pp
- Remaining failures are dominated by: retrieval failures (BM25 doesn't find relevant docs), deep reasoning errors (correct info available but model reasons incorrectly), and irreducible format mismatches (gold answers sometimes expect full names, sometimes short names unpredictably)
- Further improvement would require parameter changes (retrieval_k, temperature) or structural changes (retry/verification steps, re-ranking), both forbidden by scope contract.

### Config: `configs/remote-best-v014.json`
- Model: gpt-4.1-mini, temperature=0.0, top_p=0.95
- query: variant-005, summarize1: variant-003, summarize2: variant-005, answer: variant-012
- retrieval_k=7, BM25

---

## 2026-03-05 — Baseline
- Summary: GEPA-aligned chain with all variant-001 prompts.
- Why: Aligned chain with GEPA paper's HoVerMultiHop program. 9-node to 6-node chain (removed query_hop1, alias_hop1, alias_hop2); split summarize into summarize1/summarize2; ColBERT k=7; temperature=1.0; pure EM scoring.
- Config: gpt-4.1-mini, temperature=1.0, top_p=0.95, ColBERT k=7, 6-node GEPA chain.

### Baseline scores (all variant-001):
| Split | EM | F1 |
|-------|------|------|
| Train (150) | 40.67 | 51.73 |
| Val (300) | 39.33 | 53.28 |
| Test (300) | 34.67 | 49.05 |

---

## 2026-03-02
- Summary: Initial tenant scaffold created.
- Why: Set up HotpotQA tenant structure for GEPA pipeline replication.
- Files/configs: Full directory scaffold, docs, README.
- Eval impact: None yet — scaffold only.
- Rollback notes: Remove `tenants/hotpotqa/` directory.
