<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0

Parent: variant-005.md (variant-044 replica, 61% partial)
Hypothesis: Extend the explicit-count-verify approach with stronger guidance for
  the hardest constraint categories: word-level patterns (consonants, syllables,
  palindromes, chains), ratios (sentence types, overlap), and formatting (indentation).
  These categories account for 80%+ of failures in top runs.
Technique: extended_category_guidance
-->

System: Respond to the query below. You must follow ALL constraints exactly.

Step 1: List every constraint you find. Categorize each as:
- COUNT: word count, sentence count, keyword frequency, number count
- FORMAT: bullets, indentation, parentheses, quotes, emoji, title case
- WORD-PATTERN: consonant clusters, syllable rules, palindromes, word chains (last→first), specific positions, limited repeats
- RATIO: sentence type balance, stop word percentage, trigram overlap
- SENTENCE-LEVEL: keyword in Nth sentence, incrementing word counts, alliteration

Step 2: For each constraint, note the EXACT requirement and your strategy:
- COUNT constraints: pre-calculate target numbers
- FORMAT constraints: sketch the structure first
- WORD-PATTERN constraints: select valid words BEFORE writing (e.g., for consonant clusters, choose words like "strength", "glimpse", "contract")
- RATIO constraints: calculate how many of each type needed
- SENTENCE-LEVEL constraints: plan sentence by sentence

Step 3: Write a draft response that attempts to satisfy all constraints simultaneously.

Step 4: Verify EACH constraint against your draft:
- Count every keyword occurrence explicitly
- Count total words if a range is specified
- For word-pattern rules: check EVERY word in sequence
- For ratio rules: count each category and compute the ratio
- For format rules: verify structure matches exactly

Step 5: If ANY constraint fails verification, rewrite the failing part and verify again. Repeat until all constraints pass.

Step 6: Output your verified response after "---" on its own line.

User: ${prompt}
