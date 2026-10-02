from __future__ import annotations

from retrace.errors import RetraceError
from retrace.models import ALLOWED_PANELS, UIPlan

_FORBIDDEN_WORDS = ("approve", "delete", "drop table", "execute", "grant", "ignore previous", "run the", "sql", "<script")


def catalogue() -> dict:
    return {
        "version": 1,
        "panels": list(ALLOWED_PANELS),
        "authority": "The prompt bar may only reorder these panels. It cannot approve, run, delete, or share.",
    }


def parse_prompt(prompt: str) -> dict:
    text = " ".join(prompt.split())
    if not text:
        raise RetraceError(
            "empty_prompt",
            "The workspace prompt was empty.",
            "Ask for a layout, such as “compare the repair and the checks”.",
        )
    if len(text) > 400:
        raise RetraceError(
            "prompt_too_long",
            "The workspace prompt is longer than 400 characters.",
            "Ask for one layout change.",
        )
    lowered = text.lower()
    if any(word in lowered for word in _FORBIDDEN_WORDS):
        raise RetraceError(
            "prompt_not_a_layout",
            "The prompt bar arranges the workspace. It does not approve, run, delete, or send anything.",
            "Use the review and run controls for those actions.",
            status=422,
        )
    if any(token in lowered for token in ("lineage", "graph", "relationship")):
        plan = UIPlan(version=1, panels=["lineage", "brief"], inspector=True, focus="lineage")
        note = "Lineage and the case brief."
    elif any(token in lowered for token in ("compare", "check", "repair", "proposal")):
        plan = UIPlan(version=1, panels=["proposal", "checks"], inspector=True, focus="checks")
        note = "The repair beside its checks."
    elif any(token in lowered for token in ("evidence", "bundle", "handover", "export")):
        plan = UIPlan(version=1, panels=["evidence", "checks"], inspector=True, focus="evidence")
        note = "The evidence bundle and the checks it carries."
    elif "notebook" in lowered or "code" in lowered:
        plan = UIPlan(version=1, panels=["notebook", "proposal"], inspector=True, focus="notebook")
        note = "The notebook and the proposed change."
    else:
        raise RetraceError(
            "unsupported_layout",
            "That request is not in the workspace catalogue.",
            "Ask to see the notebook, the comparison, the lineage, or the evidence.",
            status=422,
        )
    return {"plan": plan.model_dump(), "note": note, "author": "deterministic-layout", "model": "none"}


def validate_plan(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise RetraceError("bad_plan", "The layout plan is not an object.", "Choose panels from the catalogue.")
    try:
        plan = UIPlan.model_validate(payload)
    except Exception as exc:  # noqa: BLE001 — pydantic error becomes a product message
        raise RetraceError(
            "bad_plan",
            "The layout plan does not match the workspace catalogue.",
            "Use only the listed panels. Layout plans cannot carry actions or code.",
            status=422,
        ) from exc
    unknown = [panel for panel in plan.panels if panel not in ALLOWED_PANELS]
    if unknown or len(set(plan.panels)) != len(plan.panels):
        raise RetraceError(
            "bad_plan",
            "The layout names a panel that is not in the catalogue, or names one twice.",
            "Choose each panel at most once from the catalogue.",
            status=422,
        )
    if plan.focus is not None and plan.focus not in ALLOWED_PANELS:
        raise RetraceError(
            "bad_plan",
            "The focused panel is not in the catalogue.",
            "Focus a listed panel, or leave focus empty.",
            status=422,
        )
    return plan.model_dump()
