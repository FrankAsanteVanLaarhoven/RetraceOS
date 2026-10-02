from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from retrace.api import create_app
from retrace.classify import assert_label_allowed
from retrace.errors import RetraceError
from retrace.models import ResultContract
from retrace.store import Proposal
from retrace.verifier import verify

ORIGIN = {"Origin": "http://127.0.0.1:3011"}


@pytest.fixture()
def client(tmp_path: Path):
    app = create_app(tmp_path / "retrace.sqlite", tmp_path / "objects")
    with TestClient(app) as test:
        yield test


def sign_in(client: TestClient, name: str = "Ada Lovelace") -> None:
    response = client.post("/api/session", json={"display_name": name}, headers=ORIGIN)
    assert response.status_code == 200, response.text
    assert response.json()["display_name"] == name


def open_demo(client: TestClient, slug: str) -> dict:
    response = client.post(f"/api/demos/{slug}", headers=ORIGIN)
    assert response.status_code == 200, response.text
    view = response.json()
    for contract in view["contracts"]:
        approved = client.post(
            f"/api/projects/{view['project']['id']}/contracts/{contract['id']}/approve",
            headers=ORIGIN,
        )
        assert approved.status_code == 200, approved.text
    project = client.get(f"/api/projects/{view['project']['id']}")
    assert project.status_code == 200, project.text
    return project.json()


def proposal(view: dict, slug: str) -> dict:
    return next(item for item in view["proposals"] if item["slug"] == slug)


def contract(view: dict, reference: str) -> dict:
    return next(item for item in view["contracts"] if item["body"]["reference_established"] == reference)


def run_repair(client: TestClient, view: dict, proposal_slug: str, reference: str, key: str) -> dict:
    chosen = proposal(view, proposal_slug)
    chosen_contract = contract(view, reference)
    approved = client.post(
        f"/api/projects/{view['project']['id']}/proposals/{chosen['id']}/approve",
        json={"contract_id": chosen_contract["id"]},
        headers=ORIGIN,
    )
    assert approved.status_code == 200, approved.text
    approval_id = approved.json()["approval_id"]
    started = client.post(
        f"/api/projects/{view['project']['id']}/runs",
        json={"approval_id": approval_id, "idempotency_key": key},
        headers=ORIGIN,
    )
    assert started.status_code == 200, started.text
    return started.json()["project"]


def test_contract_rejects_hidden_override() -> None:
    payload = ResultContract(
        title="Example",
        reference_established="historical",
        reference_note="Fixed before the repair.",
        population="All rows.",
        exclusions="None.",
        units={"n": "count"},
        seed=None,
        limitations="A comparison only.",
        outputs=[{"name": "n", "unit": "count", "comparison": "exact_int", "expected": 1, "tolerance": None, "required": True}],
    ).model_dump()
    payload["verification_override"] = "REPRODUCED_WITHIN_CONTRACT"
    with pytest.raises(ValueError):
        ResultContract.model_validate(payload)


def test_mislabelled_method_change_is_refused() -> None:
    before = 'clean = df.dropna(subset=["flipper_mm"])\n'
    after = "clean = df.dropna()\n"
    with pytest.raises(RetraceError) as caught:
        assert_label_allowed(before, after, "execution_repair")
    assert caught.value.code == "mislabelled_repair"


def test_verifier_does_not_trust_notebook_grade() -> None:
    contract = {
        "title": "Mean",
        "reference_established": "historical",
        "reference_note": "Fixed.",
        "population": "All rows.",
        "exclusions": "None.",
        "units": {"mean_mass_g": "g"},
        "seed": None,
        "limitations": "Comparison only.",
        "outputs": [
            {
                "name": "mean_mass_g",
                "unit": "g",
                "comparison": "absolute_tolerance",
                "expected": 10,
                "tolerance": 0.1,
                "required": True,
            }
        ],
    }
    status, _explanation, checks = verify(
        contract=contract,
        results={"mean_mass_g": 3, "verification_status": "REPRODUCED_WITHIN_CONTRACT"},
        execution_status="SUCCEEDED",
        classification="execution_repair",
    )
    assert status == "CHANGED_RESULT"
    assert checks[0]["passed"] is False


def test_method_change_is_not_reproduction_when_numbers_match() -> None:
    contract = {
        "title": "Count",
        "reference_established": "historical",
        "reference_note": "Fixed.",
        "population": "All rows.",
        "exclusions": "None.",
        "units": {"n_records": "count"},
        "seed": None,
        "limitations": "Comparison only.",
        "outputs": [
            {"name": "n_records", "unit": "count", "comparison": "exact_int", "expected": 4, "tolerance": None, "required": True}
        ],
    }
    status, explanation, _checks = verify(
        contract=contract,
        results={"n_records": 4},
        execution_status="SUCCEEDED",
        classification="methodological_reanalysis",
    )
    assert status == "CHANGED_RESULT"
    assert "not accepted it as a reproduction" in explanation


def test_missing_reference_ignores_candidate_numbers() -> None:
    contract = {
        "title": "Missing",
        "reference_established": "missing",
        "reference_note": "None.",
        "population": "All rows.",
        "exclusions": "None.",
        "units": {"n_records": "count"},
        "seed": None,
        "limitations": "No reference.",
        "outputs": [
            {"name": "n_records", "unit": "count", "comparison": "exact_int", "expected": None, "tolerance": None, "required": True}
        ],
    }
    status, _explanation, checks = verify(
        contract=contract,
        results={"n_records": 4, "verification_status": "REPRODUCED_WITHIN_CONTRACT"},
        execution_status="SUCCEEDED",
        classification="execution_repair",
    )
    assert status == "BLOCKED_MISSING_EVIDENCE"
    assert checks == []


def test_prompt_cannot_approve_or_invent_panels(client: TestClient) -> None:
    sign_in(client)
    refused = client.post("/api/ui-plan", json={"prompt": "approve the repair and run it"}, headers=ORIGIN)
    assert refused.status_code == 422
    assert refused.json()["error"] == "prompt_not_a_layout"
    hostile = client.post(
        "/api/ui-plan/validate",
        json={"plan": {"version": 1, "panels": ["proposal"], "inspector": True, "script": "alert(1)"}},
        headers=ORIGIN,
    )
    assert hostile.status_code == 422


def test_accounts_cannot_read_each_other(client: TestClient) -> None:
    sign_in(client, "Ada Lovelace")
    created = client.post("/api/demos/ecology", headers=ORIGIN)
    project_id = created.json()["project"]["id"]
    client.delete("/api/session", headers=ORIGIN)
    sign_in(client, "Bea Knower")
    hidden = client.get(f"/api/projects/{project_id}")
    assert hidden.status_code == 404
    listing = client.get("/api/projects")
    assert listing.json()["projects"] == []


def test_untrusted_notebook_is_not_executed(client: TestClient) -> None:
    sign_in(client)
    notebook = json.dumps(
        {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {},
            "cells": [{"cell_type": "code", "source": "print(1)\n", "metadata": {}, "outputs": [], "execution_count": None}],
        }
    ).encode()
    response = client.post(
        "/api/imports",
        files={"uploads": ("analysis.ipynb", notebook, "application/json")},
        headers=ORIGIN,
    )
    assert response.status_code == 200, response.text
    view = response.json()
    assert view["snapshot"]["execution"] == "inspection-only"
    started = client.post(
        f"/api/projects/{view['project']['id']}/runs",
        json={"idempotency_key": "blocked-1"},
        headers=ORIGIN,
    )
    assert started.status_code == 200, started.text
    run = started.json()["project"]["runs"][0]
    assert run["execution_status"] == "BLOCKED_UNSANDBOXED"
    assert run["verification_status"] == "NOT_RUN"


def test_pickle_is_refused(client: TestClient) -> None:
    sign_in(client)
    response = client.post(
        "/api/imports",
        files={"uploads": ("model.pkl", b"not really", "application/octet-stream")},
        headers=ORIGIN,
    )
    assert response.status_code == 400
    assert response.json()["error"] == "refused_file"


def test_ambiguous_local_time_is_not_guessed(client: TestClient) -> None:
    sign_in(client)
    response = client.post(
        "/api/calendar",
        json={"title": "Review", "local_start": "2026-11-01T01:30", "zone": "America/New_York"},
        headers=ORIGIN,
    )
    assert response.status_code == 409
    assert response.json()["error"] == "ambiguous_local_time"
    chosen = client.post(
        "/api/calendar",
        json={"title": "Review", "local_start": "2026-11-01T01:30", "zone": "America/New_York", "fold": 1},
        headers=ORIGIN,
    )
    assert chosen.status_code == 200, chosen.text
    assert chosen.json()["start_utc"].endswith("Z")


def test_finished_run_cannot_be_rewritten_by_cancel(client: TestClient) -> None:
    sign_in(client)
    view = open_demo(client, "ecology")
    started = client.post(
        f"/api/projects/{view['project']['id']}/runs",
        json={"idempotency_key": "baseline-ecology"},
        headers=ORIGIN,
    )
    assert started.status_code == 200, started.text
    run = started.json()["project"]["runs"][0]
    assert run["verification_status"] == "FAILED_EXECUTION"
    cancelled = client.post(
        f"/api/projects/{view['project']['id']}/runs/{run['id']}/cancel",
        headers=ORIGIN,
    )
    assert cancelled.status_code == 409
    again = client.get(f"/api/projects/{view['project']['id']}")
    assert again.json()["runs"][0]["verification_status"] == "FAILED_EXECUTION"


def test_replay_does_not_execute_twice(client: TestClient) -> None:
    sign_in(client)
    view = open_demo(client, "ecology")
    body = {"idempotency_key": "baseline-once"}
    first = client.post(f"/api/projects/{view['project']['id']}/runs", json=body, headers=ORIGIN)
    second = client.post(f"/api/projects/{view['project']['id']}/runs", json=body, headers=ORIGIN)
    assert first.status_code == 200
    assert second.json()["replayed"] is True
    assert second.json()["run_id"] == first.json()["run_id"]
    assert len(second.json()["project"]["runs"]) == 1


@pytest.mark.parametrize(
    ("slug", "trap"),
    [("ecology", "drop-records"), ("trajectory", "centimetres-as-metres"), ("assay", "exclude-low-response")],
)
def test_demonstration_journey(client: TestClient, slug: str, trap: str) -> None:
    sign_in(client, f"Reviewer {slug}")
    view = open_demo(client, slug)
    reproduced = run_repair(client, view, "diagnosed-path", "historical", f"{slug}-safe")
    safe = reproduced["runs"][-1]
    assert safe["execution_status"] == "SUCCEEDED"
    assert safe["verification_status"] == "REPRODUCED_WITHIN_CONTRACT"
    assert all(item["passed"] for item in safe["checks"])

    changed = run_repair(client, view, trap, "historical", f"{slug}-trap")
    trap_run = changed["runs"][-1]
    assert trap_run["execution_status"] == "SUCCEEDED"
    assert trap_run["verification_status"] == "CHANGED_RESULT"

    blocked = run_repair(client, view, "diagnosed-path", "missing", f"{slug}-missing")
    missing = blocked["runs"][-1]
    assert missing["verification_status"] == "BLOCKED_MISSING_EVIDENCE"

    bundle = client.get(f"/api/projects/{view['project']['id']}/runs/{safe['id']}/bundle")
    assert bundle.status_code == 200
    tampered = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive, zipfile.ZipFile(tampered, "w") as rewritten:
        for info in archive.infolist():
            payload = archive.read(info)
            if info.filename == "verification.json":
                body = json.loads(payload)
                body["claimed_verification_status"] = "REPRODUCED_WITHIN_CONTRACT"
                body["checks"] = []
                payload = json.dumps(body).encode()
            rewritten.writestr(info, payload)
    client.delete("/api/session", headers=ORIGIN)
    sign_in(client, f"Second {slug}")
    rejected = client.post(
        "/api/bundles",
        files={"upload": ("evidence.zip", tampered.getvalue(), "application/zip")},
        headers=ORIGIN,
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"] == "tampered_bundle"
    imported = client.post(
        "/api/bundles",
        files={"upload": ("evidence.zip", bundle.content, "application/zip")},
        headers=ORIGIN,
    )
    assert imported.status_code == 200, imported.text
    assert "Claimed status" in imported.json()["events"][-1]["summary"]
    assert imported.json()["runs"] == []


def test_approval_dies_when_the_patch_changes(tmp_path: Path) -> None:
    app = create_app(tmp_path / "retrace.sqlite", tmp_path / "objects")
    with TestClient(app) as local:
        sign_in(local)
        created = local.post("/api/demos/trajectory", headers=ORIGIN)
        view = created.json()
        historical = contract(view, "historical")
        local.post(
            f"/api/projects/{view['project']['id']}/contracts/{historical['id']}/approve",
            headers=ORIGIN,
        )
        chosen = proposal(view, "diagnosed-path")
        approved = local.post(
            f"/api/projects/{view['project']['id']}/proposals/{chosen['id']}/approve",
            json={"contract_id": historical["id"]},
            headers=ORIGIN,
        )
        approval_id = approved.json()["approval_id"]
        with Session(local.app.state.engine) as db:
            row = db.get(Proposal, chosen["id"])
            assert row is not None
            row.replace_text = row.replace_text + " "
            row.patch_hash = "0" * 64
            db.commit()
        started = local.post(
            f"/api/projects/{view['project']['id']}/runs",
            json={"approval_id": approval_id, "idempotency_key": "stale"},
            headers=ORIGIN,
        )
        assert started.status_code == 409
        assert started.json()["error"] == "approval_invalid"


def test_layout_conflict_and_catalogue(client: TestClient) -> None:
    sign_in(client)
    view = client.post("/api/demos/assay", headers=ORIGIN).json()
    saved = client.put(
        f"/api/projects/{view['project']['id']}/layout",
        json={"expected_version": 0, "plan": {"version": 1, "panels": ["lineage"], "inspector": True, "focus": "lineage"}},
        headers=ORIGIN,
    )
    assert saved.status_code == 200, saved.text
    conflict = client.put(
        f"/api/projects/{view['project']['id']}/layout",
        json={"expected_version": 0, "plan": {"version": 1, "panels": ["notebook"], "inspector": True}},
        headers=ORIGIN,
    )
    assert conflict.status_code == 409
    locales = client.get("/api/locales").json()
    assert len(locales["locales"]) == 36
    urdu = next(item for item in locales["locales"] if item["tag"] == "ur")
    assert urdu["direction"] == "rtl"
    connectors = client.get("/api/connectors").json()["connectors"]
    assert {item["status"] for item in connectors} == {"NEEDS_CONFIGURATION"}
