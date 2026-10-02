from __future__ import annotations

import math
from typing import Any

from retrace.models import ResultContract


def _as_contract(contract: dict[str, Any] | ResultContract) -> ResultContract:
    if isinstance(contract, ResultContract):
        return contract
    return ResultContract.model_validate(contract)


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def verify(
    *,
    contract: dict[str, Any] | ResultContract,
    results: dict[str, Any] | None,
    execution_status: str,
    classification: str,
    malformed_output: bool = False,
) -> tuple[str, str, list[dict[str, Any]]]:
    """Independent comparison. The repair worker does not call this to set its own grade.

    A value named verification_status inside the notebook output is ignored.
    """

    if execution_status == "CANCELLED":
        return (
            "NOT_RUN",
            "The run was cancelled before execution. No result was produced.",
            [],
        )
    if execution_status == "BLOCKED_UNSANDBOXED":
        return (
            "NOT_RUN",
            "Execution was refused. This workstation profile only runs admitted demonstration notebooks, because no tested sandbox is configured.",
            [],
        )
    if execution_status == "FAILED":
        return (
            "FAILED_EXECUTION",
            "The notebook stopped with an error. That is an execution failure, not a reproduced result.",
            [],
        )

    body = _as_contract(contract)
    if body.reference_established == "missing" or any(
        item.required and item.expected is None for item in body.outputs
    ):
        return (
            "BLOCKED_MISSING_EVIDENCE",
            "A required reference is missing. The run cannot be called reproduced, and the notebook output was not used to fill the gap.",
            [],
        )
    if body.reference_established == "newly_established":
        return (
            "EXECUTED_NOT_VERIFIED",
            "This contract records a new reference. It does not claim to reproduce an earlier result.",
            [],
        )
    if malformed_output or results is None:
        return (
            "EXECUTED_NOT_VERIFIED",
            "The notebook finished without a readable outputs/results.json object. Nothing was verified.",
            [],
        )

    checks: list[dict[str, Any]] = []
    for item in body.outputs:
        if not item.required:
            continue
        actual = results.get(item.name)
        number = _finite_number(actual)
        if item.comparison == "exact_int":
            passed = isinstance(actual, int) and not isinstance(actual, bool) and actual == item.expected
            detail = "Exact integer comparison."
        else:
            tolerance = 0.0 if item.tolerance is None else float(item.tolerance)
            expected = _finite_number(item.expected)
            passed = number is not None and expected is not None and abs(number - expected) <= tolerance
            detail = f"Absolute tolerance {tolerance} {item.unit}."
        checks.append(
            {
                "name": item.name,
                "unit": item.unit,
                "passed": passed,
                "expected": None if item.expected is None else str(item.expected),
                "actual": None if actual is None else str(actual),
                "detail": detail if passed or number is not None or item.comparison == "exact_int" else "The output was missing or not a finite number.",
            }
        )

    if classification == "methodological_reanalysis":
        return (
            "CHANGED_RESULT",
            "This patch changes the analysis. RETRACE has not accepted it as a reproduction, even where a number still matches.",
            checks,
        )
    if checks and all(item["passed"] for item in checks):
        return (
            "REPRODUCED_WITHIN_CONTRACT",
            "The declared outputs agree with the approved contract. This is only that comparison. It does not show that a scientific conclusion is correct.",
            checks,
        )
    return (
        "CHANGED_RESULT",
        "The notebook ran, and at least one declared check failed. The result is not the approved comparison.",
        checks,
    )
