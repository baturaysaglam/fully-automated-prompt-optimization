# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0
#
# Adapted from EleutherAI lm-evaluation-harness
# (https://github.com/EleutherAI/lm-evaluation-harness)
# Original code licensed under MIT License.

"""AMPS Hard symbolic math scoring utilities."""

from __future__ import annotations

import re
import traceback
import warnings
from typing import Tuple

from ..util import last_boxed_only_string, remove_boxed

try:
    import sympy
    from sympy.parsing.latex import parse_latex
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "sympy is required for AMPS_Hard scoring. Install via: pip install sympy"
    )

try:
    import lark
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "lark is required for LaTeX parsing. Install via: pip install lark"
    )


def run_with_timeout(func, args=(), timeout=8):
    """Run a function with a timeout using threading."""
    import threading

    result_container = [None]
    exception_container = [None]

    def target():
        try:
            result_container[0] = func(*args)
        except Exception as e:
            exception_container[0] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise TimeoutError("Operation timed out")

    if exception_container[0] is not None:
        raise exception_container[0]
    return result_container[0]


def amps_hard_process_results(
    ground_truth: str, llm_answer: str, debug: bool = False
) -> Tuple[int, str]:
    """Score an AMPS Hard symbolic math answer."""
    retval = 0
    parsed_answer = None

    if isinstance(ground_truth, list):
        ground_truth = ground_truth[-1]

    # Normalize LLM answer
    llm_answer = llm_answer.replace("+C", "")
    llm_answer = llm_answer.replace("+ C", "")
    llm_answer = llm_answer.replace("+ c", "")
    llm_answer = llm_answer.replace("+c", "")
    llm_answer = llm_answer.replace("\\\\fbox{", "\\\\boxed{")
    llm_answer = llm_answer.replace("\\dfrac", "\\frac")
    llm_answer = llm_answer.replace("\\tfrac", "\\frac")
    llm_answer = llm_answer.replace("\\left", "")
    llm_answer = llm_answer.replace("\\right", "")
    llm_answer = llm_answer.replace("\\bigl", "")
    llm_answer = llm_answer.replace("\\bigr", "")
    llm_answer = llm_answer.replace("\\Bigl", "")
    llm_answer = llm_answer.replace("\\Bigr", "")
    llm_answer = llm_answer.replace("\\,", "")
    llm_answer = llm_answer.replace("\\;", "")
    llm_answer = llm_answer.replace("\n", "")
    llm_answer = llm_answer.replace("\\cdot", "*")

    # Normalize ground truth
    ground_truth = ground_truth.replace("\\left", "")
    ground_truth = ground_truth.replace("\\right", "")
    ground_truth = ground_truth.replace(" ^", "^")
    ground_truth = ground_truth.replace("\\ ", "*")

    # Try to extract from \boxed{...}
    last_boxed = last_boxed_only_string(llm_answer)
    if last_boxed:
        parsed_answer = normalize_final_answer(remove_boxed(last_boxed))

    # Try to extract from last $ $ block
    if parsed_answer is None:
        last_line = llm_answer.split("\n")[-1] if "\n" in llm_answer else llm_answer
        if last_line.count("$") >= 2:
            close_pos = last_line.rfind("$")
            if close_pos > 0 and last_line[close_pos - 1] == "$":
                close_pos -= 1
            open_pos = last_line.rfind("$", 0, close_pos)
            math = last_line[open_pos + 1:close_pos]
            if "=" in math:
                math = math.split("=")[-1].strip()
            elif "\\quad \\text{or} \\quad" in math:
                math = math.split("\\quad \\text{or} \\quad")[-1].strip()
            parsed_answer = normalize_final_answer(math)

    # Compare with SymPy
    if parsed_answer is not None:
        try:
            res = run_with_timeout(is_equiv, args=(ground_truth, parsed_answer), timeout=8)
            if res:
                retval = 1
        except TimeoutError:
            warnings.warn("Timeout when comparing ground truth and parsed answer")
        except Exception as e:
            warnings.warn(f"Error when comparing: {e}")
    else:
        # Direct string match fallback
        clean = llm_answer.rstrip(".")
        if len(clean) >= len(ground_truth) and ground_truth == clean[-len(ground_truth):]:
            parsed_answer = clean[-len(ground_truth):]
            retval = 1

    if retval == 1:
        feedback_text = (
            f"Correct. Parsed answer '{parsed_answer}' is equivalent to "
            f"ground truth '{ground_truth}'."
        )
    else:
        feedback_text = (
            f"Incorrect. Parsed answer '{parsed_answer}' is not equivalent to "
            f"ground truth '{ground_truth}'. Check your notation and calculation."
        )

    return retval, feedback_text


def parse(x: str) -> list:
    """Parse a LaTeX expression into SymPy expression(s)."""
    try:
        parsed_xs = parse_latex(x, backend="lark")
    except Exception:
        try:
            parsed_xs = parse_latex(x.replace("\\\\", "\\"), backend="lark")
        except Exception:
            try:
                parsed_xs = parse_latex(x)
            except Exception:
                warnings.warn(f"couldn't parse {x}")
                return []

    if isinstance(parsed_xs, lark.Tree):
        parsed_xs = parsed_xs.children
    else:
        parsed_xs = [parsed_xs]
    return parsed_xs


def is_equiv(x1: str, x2: str) -> bool:
    """Check if two normalized LaTeX strings are mathematically equivalent."""
    try:
        parsed_x1s = parse(x1)
        parsed_x2s = parse(x2)

        if not parsed_x1s or not parsed_x2s:
            return False

        for parsed_x1 in parsed_x1s:
            for parsed_x2 in parsed_x2s:
                try:
                    diff = parsed_x1 - parsed_x2
                except Exception:
                    continue

                try:
                    if sympy.simplify(diff) == 0:
                        return True
                except Exception:
                    pass

                try:
                    if sympy.Abs(sympy.simplify(diff)) < 0.001:
                        return True
                except Exception:
                    pass

        return False
    except ImportError:
        raise
    except Exception as e:
        warnings.warn(f"Failed comparing {x1} and {x2}: {e}")
        traceback.print_tb(e.__traceback__)
        return False


def normalize_final_answer(final_answer: str) -> str:
    """Normalize a final answer (from Lewkowycz et al. 2022, Appendix D)."""
    final_answer = final_answer.split("=")[-1]

    final_answer = re.sub(r"(.*?)(\$)(.*?)(\$)(.*)", "$\\3$", final_answer)
    final_answer = re.sub(r"(\\text\{)(.*?)(\})", "\\2", final_answer)
    final_answer = re.sub(r"(\\textbf\{)(.*?)(\})", "\\2", final_answer)
    final_answer = re.sub(r"(\\overline\{)(.*?)(\})", "\\2", final_answer)
    final_answer = re.sub(r"(\\boxed\{)(.*)(\})", "\\2", final_answer)

    final_answer = re.sub(r"(frac)([^{])(.)", "frac{\\2}{\\3}", final_answer)
    final_answer = re.sub(r"(sqrt)([^{\[])", "sqrt{\\2}", final_answer)
    final_answer = final_answer.replace("$", "")

    if final_answer.replace(",", "").isdigit():
        final_answer = final_answer.replace(",", "")

    return final_answer
