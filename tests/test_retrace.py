from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from retrace.api import create_app
from retrace.classify import assert_label_allowed
from retrace.errors import RetraceError
from retrace.models import ResultContract
from retrace.store import Proposal, Store
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
    by_id = {item["id"]: item for item in connectors}
    assert set(by_id) == {"github", "slack", "google_calendar", "colab", "mcp"}
    assert by_id["slack"]["status"] == "NEEDS_CONFIGURATION"
    assert "Nothing is sent to Slack" in by_id["slack"]["detail"]
    assert by_id["google_calendar"]["status"] == "NEEDS_CONFIGURATION"
    google_hrefs = {item["href"] for item in by_id["google_calendar"]["actions"]}
    assert {"/calendar", "/api/calendar.ics", "https://calendar.google.com/calendar/r"} <= google_hrefs
    assert by_id["colab"]["status"] == "NEEDS_CONFIGURATION"
    assert "Notebooks are not sent to Colab" in by_id["colab"]["detail"]
    assert by_id["mcp"]["status"] == "OPERATIONAL"
    assert "cannot run a notebook" in by_id["mcp"]["detail"]
    assert "127.0.0.1" not in by_id["mcp"]["detail"]
    assert "http" not in by_id["mcp"]["detail"]
    assert by_id["mcp"]["notes"][2].startswith("Read the name and question")
    assert by_id["github"]["status"] in {"OPERATIONAL", "NEEDS_CONFIGURATION"}
    assert "RetraceOS" not in by_id["github"]["detail"]
    if by_id["github"]["status"] == "OPERATIONAL":
        account = by_id["github"]["account"]
        assert account and account in by_id["github"]["detail"]
        assert by_id["github"]["actions"][0]["href"] == f"https://github.com/{account}"
    started = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}},
        },
    )
    assert started.status_code == 200, started.text
    assert started.json()["result"]["serverInfo"]["name"] == "RETRACE"
    listed = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {item["name"] for item in listed.json()["result"]["tools"]}
    assert names == {"retrace_health", "retrace_connectors", "retrace_projects", "retrace_project"}
    health = client.post("/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "retrace_health", "arguments": {}}})
    assert health.json()["result"]["isError"] is False
    assert "RETRACE" in health.json()["result"]["content"][0]["text"]
    refused = client.post("/mcp", json={"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "retrace_run", "arguments": {}}})
    assert refused.json()["result"]["isError"] is True
    notice = client.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert notice.status_code == 202
    dutch = next(item for item in locales["locales"] if item["tag"] == "nl")
    assert dutch["catalogue_status"] == "INTERFACE_DRAFT"
    assert dutch["linguistic_review"] == "NOT_REVIEWED"
    assert dutch["endonym"] == "Nederlands"


def _completed(args: list[str], code: int = 0, stdout: str = "", stderr: str = "") -> object:
    return type("Completed", (), {"args": args, "returncode": code, "stdout": stdout, "stderr": stderr})()


def test_export_refuses_the_application_repository() -> None:
    from retrace.connectors import export_github

    def run(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("the application repository must be refused before GitHub is called")

    with pytest.raises(RetraceError) as caught:
        export_github(
            login="FrankAsanteVanLaarhoven",
            repository="FrankAsanteVanLaarhoven/RetraceOS",
            create=True,
            files={"retrace/" + "ab" * 16 + "/README.md": "hello"},
            run=run,
        )
    assert caught.value.code == "app_repository"


def test_export_writes_a_private_repository_for_the_signed_in_account() -> None:
    from retrace.connectors import export_github

    calls: list[tuple[list[str], str | None]] = []
    state = {"created": False}

    def run(args: list[str], input_text: str | None = None, timeout: int = 20) -> object:
        calls.append((args, input_text))
        if args[:3] == ["gh", "api", "repos/ada/notes"] and "--method" not in args:
            if not state["created"]:
                return _completed(args, 1, stderr="HTTP 404")
            return _completed(
                args,
                0,
                stdout=json.dumps({"full_name": "ada/notes", "default_branch": "main", "permissions": {"push": True}}),
            )
        if args[:3] == ["gh", "repo", "create"]:
            assert args[3] == "ada/notes"
            assert "--private" in args
            assert "--public" not in args
            state["created"] = True
            return _completed(args, 0, stdout="https://github.com/ada/notes\n")
        if "/branches/" in args[2] or ("/contents/" in args[2] and "--method" not in args):
            return _completed(args, 1, stderr="HTTP 404")
        if "--method" in args:
            assert input_text is not None
            body = json.loads(input_text)
            assert body["message"] == "Export a project from RETRACE for sharing"
            assert "reproduction" not in body["message"]
            return _completed(args, 0, stdout="{}")
        raise AssertionError(args)

    result = export_github(
        login="ada",
        repository="ada/notes",
        create=True,
        files={"retrace/" + "ab" * 16 + "/README.md": "hello\n", "retrace/" + "ab" * 16 + "/notebook.ipynb": "{}\n"},
        run=run,
    )
    assert result["repository"] == "ada/notes"
    assert result["url"] == "https://github.com/ada/notes"
    assert "RetraceOS" not in result["url"]
    assert "colab.research.google.com/github/ada/notes/" in result["colab_url"]
    assert any(item[0][:3] == ["gh", "repo", "create"] for item in calls)
    puts = [json.loads(item[1] or "{}") for item in calls if item[1]]
    assert puts[0].get("branch") is None
    assert puts[1].get("branch") == "main"


def test_account_export_download_and_slack_share(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from retrace.store import ConnectorSecret

    sign_in(client, "Ada Lovelace")
    view = client.post("/api/demos/assay", headers=ORIGIN).json()
    project_id = view["project"]["id"]
    monkeypatch.setattr("retrace.api.github_login", lambda: "ada")
    refused = client.post(
        "/api/connectors/github/export",
        json={"project_id": project_id, "repository": "frankasantevanlaarhoven/RetraceOS", "create": True},
        headers=ORIGIN,
    )
    assert refused.status_code == 400, refused.text
    assert refused.json()["error"] == "app_repository"
    seen: dict[str, object] = {}

    def fake_export(**kwargs: object) -> dict[str, str]:
        seen.update(kwargs)
        return {
            "repository": "ada/notes",
            "url": "https://github.com/ada/notes",
            "notebook_url": "https://github.com/ada/notes/blob/main/retrace/" + project_id + "/notebook.ipynb",
            "colab_url": "https://colab.research.google.com/github/ada/notes/blob/main/retrace/" + project_id + "/notebook.ipynb",
            "message": "Exported to ada/notes.",
            "next": "This export does not rerun the notebook.",
        }

    monkeypatch.setattr("retrace.api.export_github", fake_export)
    exported = client.post(
        "/api/connectors/github/export",
        json={"project_id": project_id, "repository": "ada/notes", "create": False},
        headers=ORIGIN,
    )
    assert exported.status_code == 200, exported.text
    assert seen["login"] == "ada"
    assert seen["repository"] == "ada/notes"
    files = seen["files"]
    assert isinstance(files, dict)
    assert any(path.endswith(".ipynb") for path in files)
    assert "not a reproduction result" in next(text for path, text in files.items() if path.endswith("README.md"))
    notebook = client.get(f"/api/projects/{project_id}/notebook")
    assert notebook.status_code == 200, notebook.text
    assert notebook.headers["content-type"].startswith("application/x-ipynb+json")
    assert "attachment;" in notebook.headers["content-disposition"]
    assert notebook.text.lstrip().startswith("{")

    def fake_probe(token: str) -> dict[str, str] | None:
        return {"team": "Ada Lab"} if token == "xoxb-test-token" else None

    sent: dict[str, str] = {}

    def fake_post(token: str, channel: str, text: str) -> None:
        sent["token"] = token
        sent["channel"] = channel
        sent["text"] = text

    monkeypatch.setattr("retrace.connectors.probe_slack", fake_probe)
    monkeypatch.setattr("retrace.api.probe_slack", fake_probe)
    monkeypatch.setattr("retrace.api.post_slack", fake_post)
    connected = client.post("/api/connectors/slack", json={"token": "xoxb-test-token"}, headers=ORIGIN)
    assert connected.status_code == 200, connected.text
    assert "xoxb-test-token" not in connected.text
    assert connected.json()["account"] == "Ada Lab"
    assert connected.json()["status"] == "OPERATIONAL"
    store = client.app.state.service.store
    with store.session() as db:
        saved = db.get(ConnectorSecret, (client.app.state.service.principal_from_token(client.cookies.get("retrace_session"))["id"], "slack"))
        assert saved is not None
        assert saved.secret == "xoxb-test-token"
    shared = client.post(
        "/api/connectors/slack/share",
        json={"project_id": project_id, "channel": "#lab-notes"},
        headers=ORIGIN,
    )
    assert shared.status_code == 200, shared.text
    assert "xoxb-test-token" not in shared.text
    assert sent["token"] == "xoxb-test-token"
    assert sent["channel"] == "lab-notes"
    assert "not a reproduction result" in sent["text"]
    assert "notebook" in sent["text"].lower()
    sign_in(client, "Grace Hopper")
    denied = client.get(f"/api/projects/{project_id}/notebook")
    assert denied.status_code == 404
    denied_export = client.post(
        "/api/connectors/github/export",
        json={"project_id": project_id, "repository": "ada/notes", "create": False},
        headers=ORIGIN,
    )
    assert denied_export.status_code == 404


def test_mcp_reads_only_the_signed_in_projects(client: TestClient) -> None:
    sign_in(client, "Ada Lovelace")
    ada = client.post("/api/demos/assay", headers=ORIGIN).json()
    ada_id = ada["project"]["id"]
    listed = client.get("/api/connectors")
    assert listed.status_code == 200
    assert "Bearer" not in listed.text
    assert "127.0.0.1" not in listed.text
    store = client.app.state.service.store
    principal = client.app.state.service.principal_from_token(client.cookies.get("retrace_session"))
    assert principal is not None
    config_path = store.database.parent / "mcp" / f"{principal['id']}.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    header = {"Authorization": config["authorization"]}
    assert config["authorization"] not in listed.text
    with TestClient(client.app) as stranger:
        blocked = stranger.post("/mcp", json={"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "retrace_projects", "arguments": {}}})
    assert blocked.json()["result"]["isError"] is True
    assert "Assay table" not in blocked.json()["result"]["content"][0]["text"]
    opened = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "retrace_projects", "arguments": {}}},
        headers=header,
    )
    assert opened.status_code == 200, opened.text
    assert opened.json()["result"]["isError"] is False
    assert "Assay table" in opened.json()["result"]["content"][0]["text"]
    one = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "retrace_project", "arguments": {"project_id": ada_id}}},
        headers=header,
    )
    body = json.loads(one.json()["result"]["content"][0]["text"])
    assert body["name"] == "Assay table"
    assert body["note"].endswith("not a reproduction result.")
    assert "cells" not in one.text
    sign_in(client, "Grace Hopper")
    grace = client.post("/api/demos/ecology", headers=ORIGIN).json()
    foreign = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"name": "retrace_project", "arguments": {"project_id": grace["project"]["id"]}}},
        headers=header,
    )
    assert foreign.json()["result"]["isError"] is True
    assert "Ecology measurements" not in foreign.json()["result"]["content"][0]["text"]


def test_preferences_round_trip_locale(client: TestClient) -> None:
    sign_in(client)
    saved = client.put(
        "/api/preferences",
        json={"theme": "dark", "density": "compact", "zone": "Europe/London", "locale": "ur"},
        headers=ORIGIN,
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["locale"] == "ur"
    assert saved.json()["theme"] == "dark"
    kept = client.put(
        "/api/preferences",
        json={"theme": "light", "density": "comfortable", "zone": "UTC"},
        headers=ORIGIN,
    )
    assert kept.status_code == 200, kept.text
    assert kept.json()["locale"] == "ur"
    assert kept.json()["theme"] == "light"
    rejected = client.put(
        "/api/preferences",
        json={"theme": "light", "density": "comfortable", "zone": "UTC", "locale": "xx"},
        headers=ORIGIN,
    )
    assert rejected.status_code == 400
    assert rejected.json()["error"] == "bad_locale"
    visible = client.get("/api/preferences")
    assert visible.status_code == 200
    assert visible.json()["signed_in"] is True
    assert visible.json()["locale"] == "ur"


def test_preferences_without_a_session_do_not_require_sign_in(client: TestClient) -> None:
    response = client.get("/api/preferences")
    assert response.status_code == 200
    body = response.json()
    assert body["signed_in"] is False
    assert body["locale"] == "en"
    assert body["theme"] == "system"


def test_existing_preferences_gain_locale(tmp_path: Path) -> None:
    database = tmp_path / "old.sqlite"
    engine = create_engine(f"sqlite:///{database}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE preferences (principal_id VARCHAR(36) PRIMARY KEY, theme VARCHAR(20), density VARCHAR(20), zone VARCHAR(80))"
        )
        connection.exec_driver_sql("INSERT INTO preferences (principal_id, theme, density, zone) VALUES ('p', 'dark', 'compact', 'UTC')")
    Store(database, tmp_path / "objects")
    with engine.connect() as connection:
        names = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(preferences)")}
        assert "locale" in names
        assert connection.exec_driver_sql("SELECT locale FROM preferences").scalar() == "en"
