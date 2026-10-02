from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OutputExpect(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    unit: str = Field(min_length=1, max_length=40)
    comparison: Literal["absolute_tolerance", "exact_int"]
    expected: float | int | None
    tolerance: float | None = None
    required: bool = True


class ResultContract(BaseModel):
    """Researcher-approved comparison. Extra fields are rejected so a repair payload cannot ride along."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    reference_established: Literal["historical", "newly_established", "missing"]
    reference_note: str = Field(min_length=1, max_length=2000)
    population: str = Field(min_length=1, max_length=2000)
    exclusions: str = Field(min_length=1, max_length=2000)
    units: dict[str, str]
    seed: int | None = None
    limitations: str = Field(min_length=1, max_length=4000)
    outputs: list[OutputExpect] = Field(max_length=20)


class UIPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1]
    panels: list[str] = Field(max_length=6)
    inspector: bool = True
    focus: str | None = None


ALLOWED_PANELS = ("brief", "notebook", "proposal", "checks", "lineage", "evidence")

EXECUTION_STATUSES = (
    "SUCCEEDED",
    "FAILED",
    "BLOCKED_UNSANDBOXED",
    "CANCELLED",
)

VERIFICATION_STATUSES = (
    "REPRODUCED_WITHIN_CONTRACT",
    "EXECUTED_NOT_VERIFIED",
    "CHANGED_RESULT",
    "BLOCKED_MISSING_EVIDENCE",
    "FAILED_EXECUTION",
    "NOT_RUN",
)
