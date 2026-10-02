from __future__ import annotations

import json
import os
import time
from importlib import resources
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from retrace import __version__
from retrace.errors import RetraceError
from retrace.store import Store
from retrace.uiplan import catalogue, parse_prompt, validate_plan
from retrace.workflow import Service

_ORIGINS = {
    "http://127.0.0.1:3011",
    "http://localhost:3011",
    "http://testserver",
}
_HITS: dict[str, list[float]] = {}


def locales() -> list[dict]:
    raw = resources.files("retrace").joinpath("locales.json").read_text(encoding="utf-8")
    return json.loads(raw)


def capabilities() -> dict:
    def model_state(name: str) -> str:
        if os.environ.get(name):
            return "CONFIGURED_NOT_USED"
        return "NEEDS_CONFIGURATION"

    return {
        "product": "RETRACE",
        "version": __version__,
        "profile": "workstation-local",
        "release_decision": "REVISE",
        "sandbox": "Curated demonstration notebooks only. No tested sandbox is configured, so other notebooks are refused.",
        "database": "SQLite with application-enforced account separation. PostgreSQL row-level security is not claimed: no PostgreSQL server is configured.",
        "models": {
            "anthropic": model_state("ANTHROPIC_API_KEY"),
            "openrouter": model_state("OPENROUTER_API_KEY"),
            "repairs": "deterministic-diagnoser",
            "note": "A configured key is not called. Notebooks and results are not sent to a model provider by this build.",
        },
        "connectors": [
            {"id": "github", "status": "NEEDS_CONFIGURATION", "detail": "No GitHub App credentials are configured."},
            {"id": "slack", "status": "NEEDS_CONFIGURATION", "detail": "No Slack workspace installation is configured."},
            {"id": "google_calendar", "status": "NEEDS_CONFIGURATION", "detail": "No Google Calendar OAuth client is configured. Internal events and ICS export work without it."},
            {"id": "colab", "status": "NEEDS_CONFIGURATION", "detail": "No Colab session is connected. This is not a hosted execution backend."},
            {"id": "mcp", "status": "NEEDS_CONFIGURATION", "detail": "RETRACE does not expose an MCP tool server in this build."},
        ],
    }


def create_app(database: Path, objects: Path) -> FastAPI:
    service = Service(Store(database, objects))
    app = FastAPI(title="RETRACE", version=__version__, docs_url=None, redoc_url=None)
    app.state.service = service
    app.state.engine = service.store.engine
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(_ORIGINS),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Origin"],
    )

    @app.exception_handler(RetraceError)
    async def on_error(_request: Request, exc: RetraceError) -> JSONResponse:
        return JSONResponse(exc.as_dict(), status_code=exc.status)

    def principal(request: Request) -> dict:
        found = service.principal_from_token(request.cookies.get("retrace_session"))
        if found is None:
            raise RetraceError(
                "sign_in_required",
                "Sign in on this workstation before opening a project.",
                "Enter a display name. This is a local session, not institutional sign-in.",
                status=401,
            )
        return found

    def guard(request: Request) -> None:
        if request.method == "GET":
            return
        origin = request.headers.get("origin")
        if origin not in _ORIGINS:
            raise RetraceError(
                "origin_rejected",
                "The request origin is not allowed to change workstation state.",
                "Open RETRACE from the local desk.",
                status=403,
            )

    def client_key(request: Request) -> str:
        return request.client.host if request.client else "local"

    def limit(request: Request) -> None:
        now = time.monotonic()
        key = client_key(request)
        bucket = [stamp for stamp in _HITS.get(key, []) if now - stamp < 60]
        if len(bucket) >= 120:
            raise RetraceError(
                "rate_limited",
                "Too many sign-in attempts from this machine.",
                "Wait a minute and try again.",
                status=429,
            )
        bucket.append(now)
        _HITS[key] = bucket

    def set_session(response: Response, token: str) -> None:
        response.set_cookie(
            "retrace_session",
            token,
            httponly=True,
            samesite="lax",
            secure=False,
            path="/",
            max_age=60 * 60 * 12,
        )

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True, "product": "RETRACE", "version": __version__}

    @app.get("/api/capabilities")
    def caps() -> dict:
        return capabilities()

    @app.get("/api/locales")
    def locale_list() -> dict:
        rows = locales()
        return {
            "locales": rows,
            "shipped_interface_locale": "en",
            "note": "Other locales are catalogued. Their interface is not translated and has not had linguistic review. Urdu is included as right-to-left.",
        }

    @app.get("/api/connectors")
    def connectors() -> dict:
        return {"connectors": capabilities()["connectors"]}

    @app.get("/api/ui-plan/catalogue")
    def ui_catalogue() -> dict:
        return catalogue()

    @app.post("/api/session")
    def sign_in(request: Request, payload: dict) -> JSONResponse:
        guard(request)
        limit(request)
        person, token = service.sign_in(str(payload.get("display_name", "")))
        response = JSONResponse({"display_name": person["display_name"]})
        set_session(response, token)
        return response

    @app.get("/api/session")
    def session(request: Request) -> dict:
        person = principal(request)
        return {"display_name": person["display_name"]}

    @app.delete("/api/session")
    def sign_out(request: Request) -> Response:
        guard(request)
        service.sign_out(request.cookies.get("retrace_session"))
        response = Response(status_code=204)
        response.delete_cookie("retrace_session", path="/")
        return response

    @app.get("/api/preferences")
    def get_preferences(request: Request) -> dict:
        return service.preferences(principal(request))

    @app.put("/api/preferences")
    def put_preferences(request: Request, payload: dict) -> dict:
        guard(request)
        return service.save_preferences(
            principal(request),
            str(payload.get("theme", "system")),
            str(payload.get("density", "comfortable")),
            str(payload.get("zone", "UTC")),
        )

    @app.get("/api/projects")
    def projects(request: Request) -> dict:
        return {"projects": service.list_projects(principal(request))}

    @app.post("/api/demos/{slug}")
    def demo(request: Request, slug: str) -> dict:
        guard(request)
        return service.seed_demo(principal(request), slug)

    @app.post("/api/imports")
    async def import_files(request: Request, uploads: list[UploadFile] = File(...)) -> dict:
        guard(request)
        files: dict[str, bytes] = {}
        for upload in uploads:
            name = upload.filename or ""
            files[name] = await upload.read()
        return service.upload(principal(request), "Imported analysis", files)

    @app.get("/api/projects/{project_id}")
    def project(request: Request, project_id: str) -> dict:
        return service.project_view(principal(request), project_id)

    @app.patch("/api/projects/{project_id}")
    def rename(request: Request, project_id: str, payload: dict) -> dict:
        guard(request)
        return service.rename_project(
            principal(request),
            project_id,
            str(payload.get("name", "")),
            int(payload.get("expected_version", -1)),
        )

    @app.post("/api/projects/{project_id}/retire")
    def retire(request: Request, project_id: str, payload: dict) -> dict:
        guard(request)
        return service.retire_project(principal(request), project_id, str(payload.get("confirmation", "")))

    @app.post("/api/projects/{project_id}/contracts/{contract_id}/approve")
    def approve_contract(request: Request, project_id: str, contract_id: str) -> dict:
        guard(request)
        return service.approve_contract(principal(request), project_id, contract_id)

    @app.post("/api/projects/{project_id}/proposals/{proposal_id}/approve")
    def approve_proposal(request: Request, project_id: str, proposal_id: str, payload: dict) -> dict:
        guard(request)
        return service.approve_proposal(
            principal(request),
            project_id,
            proposal_id,
            str(payload.get("contract_id", "")),
        )

    @app.post("/api/projects/{project_id}/runs")
    def run(request: Request, project_id: str, payload: dict) -> dict:
        guard(request)
        key = str(payload.get("idempotency_key", ""))
        approval_id = payload.get("approval_id")
        person = principal(request)
        if approval_id:
            return service.run_approval(person, project_id, str(approval_id), key)
        return service.run_baseline(person, project_id, key)

    @app.post("/api/projects/{project_id}/runs/{run_id}/cancel")
    def cancel(request: Request, project_id: str, run_id: str) -> dict:
        guard(request)
        return service.cancel_run(principal(request), project_id, run_id)

    @app.get("/api/projects/{project_id}/runs/{run_id}/bundle")
    def bundle(request: Request, project_id: str, run_id: str) -> Response:
        payload = service.export_bundle(principal(request), project_id, run_id)
        return Response(
            payload,
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="retrace-evidence.zip"'},
        )

    @app.post("/api/bundles")
    async def import_bundle(request: Request, upload: UploadFile = File(...)) -> dict:
        guard(request)
        return service.import_bundle(principal(request), await upload.read())

    @app.put("/api/projects/{project_id}/layout")
    def layout(request: Request, project_id: str, payload: dict) -> dict:
        guard(request)
        return service.save_layout(
            principal(request),
            project_id,
            payload.get("plan") or {},
            int(payload.get("expected_version", 0)),
        )

    @app.post("/api/ui-plan")
    def ui_plan(request: Request, payload: dict) -> dict:
        guard(request)
        principal(request)
        return parse_prompt(str(payload.get("prompt", "")))

    @app.post("/api/ui-plan/validate")
    def ui_validate(request: Request, payload: dict) -> dict:
        guard(request)
        principal(request)
        return {"plan": validate_plan(payload.get("plan") or {})}

    @app.post("/api/projects/{project_id}/wiki")
    def wiki(request: Request, project_id: str) -> dict:
        guard(request)
        return service.draft_wiki(principal(request), project_id)

    @app.post("/api/projects/{project_id}/wiki/review")
    def wiki_review(request: Request, project_id: str) -> dict:
        guard(request)
        return service.review_wiki(principal(request), project_id)

    @app.get("/api/calendar")
    def calendar(request: Request) -> dict:
        return {"events": service.calendar(principal(request))}

    @app.post("/api/calendar")
    def add_calendar(request: Request, payload: dict) -> dict:
        guard(request)
        fold = payload.get("fold")
        return service.add_event_time(
            principal(request),
            str(payload.get("title", "Review")),
            str(payload.get("local_start", "")),
            str(payload.get("zone", "UTC")),
            None if fold is None else int(fold),
        )

    @app.get("/api/calendar.ics")
    def calendar_ics(request: Request) -> Response:
        body = service.calendar_ics(principal(request))
        return Response(body, media_type="text/calendar")

    return app


def default_app() -> FastAPI:
    root = Path(os.environ.get("RETRACE_DATA", "data"))
    root.mkdir(parents=True, exist_ok=True)
    return create_app(root / "retrace.sqlite", root / "objects")


def main() -> None:
    import uvicorn

    uvicorn.run(default_app(), host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
