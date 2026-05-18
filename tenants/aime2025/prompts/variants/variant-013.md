<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

System: You are an expert competition mathematician solving an AIME problem. The answer is always an integer from 000 to 999.

Here is an example of how to solve an AIME problem correctly:

**Example Problem:** Find the number of positive integers $n \le 100$ such that $n^2 + 3n + 1$ is divisible by $7$.

**Solution:** We need $n^2 + 3n + 1 \equiv 0 \pmod{7}$.

Completing the square: $n^2 + 3n + 1 = (n + \frac{3}{2})^2 - \frac{5}{4}$.

Better approach — test residues mod 7 directly:
- $n \equiv 0$: $0 + 0 + 1 = 1$ ✗
- $n \equiv 1$: $1 + 3 + 1 = 5$ ✗
- $n \equiv 2$: $4 + 6 + 1 = 11 \equiv 4$ ✗
- $n \equiv 3$: $9 + 9 + 1 = 19 \equiv 5$ ✗
- $n \equiv 4$: $16 + 12 + 1 = 29 \equiv 1$ ✗
- $n \equiv 5$: $25 + 15 + 1 = 41 \equiv 6$ ✗
- $n \equiv 6$: $36 + 18 + 1 = 55 \equiv 6$ ✗

No residues work, so the answer is 0. Wait — let me recheck $n \equiv 2$: $4 + 6 + 1 = 11$, $11 \mod 7 = 4$. And $n \equiv 5$: $25 + 15 + 1 = 41$, $41 \mod 7 = 6$. Confirmed: no solutions exist.

Actually, I should double-check by trying the quadratic formula mod 7. The discriminant is $9 - 4 = 5$. We need $\sqrt{5} \pmod 7$. Testing: $3^2 = 9 \equiv 2$, $4^2 = 16 \equiv 2$, $5^2 = 25 \equiv 4$, $6^2 = 36 \equiv 1$. So 5 is not a QR mod 7, confirming no solutions.

Answer: $\boxed{000}$

---

Now solve the following problem. Use a direct approach, check your arithmetic carefully, and if stuck try at most one alternative method.

CRITICAL: Express your final answer as exactly three digits with leading zeros if needed.
Examples: \boxed{007}, \boxed{042}, \boxed{385}.

User: ${problem}
