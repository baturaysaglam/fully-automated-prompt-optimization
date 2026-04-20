#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""Bidirectional converter between DSPy optimized programs and Hephaestus prompt templates.

No DSPy dependency required — works directly with the JSON files that DSPy
saves via ``program.save()``.

Usage:
    # DSPy → Hephaestus: extract instructions from a saved DSPy program
    python convert_dspy_prompts.py dspy2heph program_dir/ --output-dir prompts/modules/

    # Hephaestus → DSPy: patch a saved DSPy program with Hephaestus template text
    python convert_dspy_prompts.py heph2dspy prompts/modules/ --program-dir program_dir/
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

# Maps DSPy predictor names (as they appear in saved program JSON keys)
# to Hephaestus prompt module directory names.
PREDICTOR_TO_MODULE: dict[str, str] = {
    "summarize1": "summarize1",
    "summarize2": "summarize2",
    "create_query_hop2": "generate_query_with_context",
    "final_answer": "generate_answer",
}

MODULE_TO_PREDICTOR: dict[str, str] = {v: k for k, v in PREDICTOR_TO_MODULE.items()}

# DSPy ChainOfThought signatures for each predictor (input_fields -> output_field).
PREDICTOR_SIGNATURES: dict[str, dict[str, Any]] = {
    "summarize1": {
        "inputs": ["question", "passages"],
        "output": "summary",
    },
    "summarize2": {
        "inputs": ["question", "context", "passages"],
        "output": "summary",
    },
    "create_query_hop2": {
        "inputs": ["question", "summary_1"],
        "output": "query",
    },
    "final_answer": {
        "inputs": ["question", "summary_1", "summary_2"],
        "output": "answer",
    },
}


def _load_dspy_program(program_dir: Path) -> dict[str, Any]:
    """Load the metadata JSON from a saved DSPy program directory."""
    meta_path = program_dir / "metadata.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    # Fallback: look for any JSON file in the directory
    json_files = sorted(program_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {program_dir}")
    return json.loads(json_files[0].read_text(encoding="utf-8"))


def _extract_instructions(program_data: dict[str, Any]) -> dict[str, str]:
    """Extract per-predictor instructions from a DSPy program's saved JSON.

    Returns a dict mapping predictor names (e.g. 'summarize1') to their
    instruction strings.
    """
    instructions: dict[str, str] = {}

    # DSPy saves predictor state under keys like "summarize1.predict" or
    # "summarize1" depending on version. Try both patterns.
    for predictor_name in PREDICTOR_TO_MODULE:
        for key_suffix in [f"{predictor_name}.predict", predictor_name]:
            if key_suffix in program_data:
                pred_data = program_data[key_suffix]
                if isinstance(pred_data, dict):
                    instr = pred_data.get("signature_instructions") or pred_data.get("instructions", "")
                    if instr:
                        instructions[predictor_name] = instr
                        break
                elif isinstance(pred_data, str):
                    instructions[predictor_name] = pred_data
                    break

    return instructions


def _generate_hephaestus_template(
    predictor_name: str,
    instruction: str,
) -> str:
    """Generate a Hephaestus .md prompt template from a DSPy instruction."""
    sig = PREDICTOR_SIGNATURES[predictor_name]
    lines = [f"System: {instruction}", ""]

    # Build the User: section with ${placeholder} variables
    user_parts = []
    for field in sig["inputs"]:
        label = field.replace("_", " ").title()
        user_parts.append(f"{label}: ${{{field}}}")

    lines.append("User: " + "\n\n".join(user_parts))
    lines.append("")

    output_label = sig["output"].replace("_", " ").title()
    lines.append(f"{output_label}:")
    lines.append("")

    return "\n".join(lines)


def _extract_system_message(template_path: Path) -> str:
    """Extract the system message text from a Hephaestus .md template."""
    text = template_path.read_text(encoding="utf-8")
    # System message is everything after "System: " until "User: " or end
    match = re.search(r"^System:\s*(.+?)(?=^User:|\Z)", text, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"No 'System:' block found in {template_path}")
    return match.group(1).strip()


def dspy_to_hephaestus(program_dir: Path, output_dir: Path) -> list[str]:
    """Convert DSPy program instructions to Hephaestus prompt templates.

    Returns list of written file paths.
    """
    program_data = _load_dspy_program(program_dir)
    instructions = _extract_instructions(program_data)

    written: list[str] = []
    for predictor_name, instruction in instructions.items():
        module_name = PREDICTOR_TO_MODULE[predictor_name]
        module_dir = output_dir / module_name
        module_dir.mkdir(parents=True, exist_ok=True)

        template = _generate_hephaestus_template(predictor_name, instruction)
        out_path = module_dir / "variant-dspy.md"
        out_path.write_text(template, encoding="utf-8")
        written.append(str(out_path))

    return written


def hephaestus_to_dspy(prompts_dir: Path, program_dir: Path) -> Path:
    """Patch a DSPy saved program with instructions from Hephaestus templates.

    Reads the latest variant from each Hephaestus module directory and writes
    a patched JSON file.

    Returns the path to the patched JSON file.
    """
    program_data = _load_dspy_program(program_dir)

    for module_name, predictor_name in MODULE_TO_PREDICTOR.items():
        module_dir = prompts_dir / module_name
        if not module_dir.exists():
            continue

        # Use the latest variant file
        variants = sorted(module_dir.glob("variant-*.md"))
        if not variants:
            continue

        system_msg = _extract_system_message(variants[-1])

        # Patch the program data
        for key_suffix in [f"{predictor_name}.predict", predictor_name]:
            if key_suffix in program_data:
                if isinstance(program_data[key_suffix], dict):
                    if "signature_instructions" in program_data[key_suffix]:
                        program_data[key_suffix]["signature_instructions"] = system_msg
                    else:
                        program_data[key_suffix]["instructions"] = system_msg
                break

    out_path = program_dir / "metadata_patched.json"
    out_path.write_text(
        json.dumps(program_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert between DSPy optimized programs and Hephaestus prompt templates.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # DSPy → Hephaestus
    d2h = subparsers.add_parser(
        "dspy2heph",
        help="Extract DSPy program instructions into Hephaestus prompt templates",
    )
    d2h.add_argument("program_dir", type=Path, help="Path to saved DSPy program directory")
    d2h.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tenants/hotpotqa/prompts/modules"),
        help="Output directory for Hephaestus prompt modules",
    )

    # Hephaestus → DSPy
    h2d = subparsers.add_parser(
        "heph2dspy",
        help="Patch a DSPy program JSON with Hephaestus template instructions",
    )
    h2d.add_argument(
        "prompts_dir",
        type=Path,
        help="Path to Hephaestus prompts/modules/ directory",
    )
    h2d.add_argument(
        "--program-dir",
        type=Path,
        required=True,
        help="Path to saved DSPy program directory to patch",
    )

    args = parser.parse_args()

    if args.command == "dspy2heph":
        written = dspy_to_hephaestus(args.program_dir, args.output_dir)
        for path in written:
            print(f"  wrote {path}")
        print(f"Converted {len(written)} predictor(s) to Hephaestus templates.")
    elif args.command == "heph2dspy":
        out = hephaestus_to_dspy(args.prompts_dir, args.program_dir)
        print(f"  wrote {out}")


if __name__ == "__main__":
    main()
