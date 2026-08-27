#!/usr/bin/env python3
"""Validate a SWAT-CUP one-simulation parameter-dictionary smoke-test log.

The script is intentionally conservative: a formal calibration should not start
unless every expected parameter was edited, SWAT completed, and post-processing
produced objective/uncertainty evidence. Static parameter-list inspection is not
accepted as proof of compatibility.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def normalize_parameter(name: str) -> str:
    value = name.strip().upper()
    value = re.sub(r"^[RVA]__", "", value)
    value = value.split(".", 1)[0]
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a captured SWAT-CUP SUFI-2 smoke-test console log."
    )
    parser.add_argument("log", type=Path, help="Path to captured console log")
    parser.add_argument(
        "--expected",
        action="append",
        default=[],
        help=(
            "Expected parameter name. Repeat this option or provide a comma-separated "
            "list, for example --expected CN2,ALPHA_BF,GW_DELAY."
        ),
    )
    parser.add_argument(
        "--allow-missing-post",
        action="store_true",
        help="Do not fail when objective/95PPU evidence is absent.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.log.is_file():
        print(json.dumps({"status": "FAIL", "reason": "LOG_NOT_FOUND"}, indent=2))
        return 2

    text = args.log.read_text(encoding="utf-8", errors="replace")
    upper = text.upper()

    expected_raw: list[str] = []
    for item in args.expected:
        expected_raw.extend(part for part in item.split(",") if part.strip())
    expected = [normalize_parameter(item) for item in expected_raw]

    parameter_lines = re.findall(r"^\s*PARAMETER:\s*([^\r\n]+)", text, re.I | re.M)
    edited = sorted({normalize_parameter(item) for item in parameter_lines})

    unsupported = sorted(
        {
            normalize_parameter(item)
            for item in re.findall(
                r'PARAMETER\s+"([^"]+)"\s+WAS\s+NOT\s+PRESENT\s+IN\s+THE\s+DICTIONARY',
                text,
                re.I,
            )
        }
    )

    dictionary_error = bool(unsupported) or "NOT PRESENT IN THE DICTIONARY" in upper
    edit_exception = "EXCEPTION HAPPENED WHILE EDITING" in upper
    swat_success = any(
        marker in upper
        for marker in (
            "EXECUTION SUCCESSFULLY COMPLETED",
            "NORMAL_FIN_SUCCESS",
            "SWAT TEST RUN: PASS",
        )
    )
    objective_success = any(
        marker in upper
        for marker in (
            "NSE",
            "95PPU",
            "OBJECTIVE FUNCTION",
            "POST_PROCESS_TEST: PASS",
            "POST PROCESS TEST: PASS",
        )
    )
    singular_matrix = "SINGULAR MATRIX" in upper

    missing_expected = sorted(set(expected) - set(edited)) if expected else []
    failures: list[str] = []
    warnings: list[str] = []

    if dictionary_error or edit_exception:
        failures.append("PARAMETER_DICTIONARY_ERROR")
    if missing_expected:
        failures.append("EXPECTED_PARAMETERS_NOT_EDITED")
    if not swat_success:
        failures.append("SWAT_DID_NOT_COMPLETE")
    if not objective_success and not args.allow_missing_post:
        failures.append("POST_OR_OBJECTIVE_EVIDENCE_MISSING")
    if singular_matrix:
        warnings.append("SINGLE_SAMPLE_SINGULAR_MATRIX_EXPECTED_IF_OTHER_GATES_PASS")

    status = "PASS" if not failures else "FAIL"
    result = {
        "status": status,
        "expected_parameters": expected,
        "edited_parameters": edited,
        "missing_expected_parameters": missing_expected,
        "unsupported_parameters": unsupported,
        "swat_completed": swat_success,
        "objective_or_95ppu_evidence": objective_success,
        "warnings": warnings,
        "failures": failures,
        "ready_for_formal_iteration": status == "PASS",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
