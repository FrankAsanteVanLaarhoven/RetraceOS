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
from retrace.connectors import (
    clean_channel,
    clean_slack_token,
    connector_rows,
    export_github,
    github_files,
    github_login,
    handle_mcp,
    notebook_filename,
    post_slack,
    probe_slack,
    slack_connector,
    slack_text,
)
from retrace.errors import RetraceError
from retrace.privacy import privacy_notice
from retrace.store import Store
from retrace.uiplan import catalogue, parse_prompt, validate_plan
from retrace.workflow import Service

_LOCAL_ORIGINS = {
    "http://127.0.0.1:3011",
    "http://localhost:3011",
    "http://testserver",
}
_HITS: dict[str, list[float]] = {}
_SIGN_IN_LIMIT = 40
_CHANGE_LIMIT = 500


def _https_origin(name: str) -> str | None:
    host = os.environ.get(name, "").strip().rstrip("/")
    if not host:
        return None
    if host.startswith("https://") or host.startswith("http://"):
        return host
    return f"https://{host}"


def allowed_origins() -> set[str]:
    extra = {item.strip().rstrip("/") for item in os.environ.get("RETRACE_ORIGINS", "").split(",") if item.strip()}
    hosted = {
        origin
        for origin in (
            _https_origin("VERCEL_URL"),
            _https_origin("VERCEL_BRANCH_URL"),
            _https_origin("VERCEL_PROJECT_PRODUCTION_URL"),
        )
        if origin
    }
    return set(_LOCAL_ORIGINS) | extra | hosted


def cookie_secure() -> bool:
    flag = os.environ.get("RETRACE_COOKIE_SECURE", "").strip()
    if flag == "1":
        return True
    if flag == "0":
        return False
    return os.environ.get("VERCEL", "").strip() == "1"


def database_url() -> str | None:
    raw = os.environ.get("RETRACE_DATABASE_URL", "").strip() or os.environ.get("POSTGRES_URL", "").strip()
    return raw or None


def database_mode() -> str:
    if database_url():
        return "operator"
    if os.environ.get("VERCEL", "").strip() == "1":
        return "ephemeral"
    return "sqlite"


def database_description() -> str:
    if database_mode() == "operator":
        return "The operator's database URL holds the records. PostgreSQL row-level security is not claimed."
    if database_mode() == "ephemeral":
        return (
            "This host has no durable database URL. Accounts and projects last only until the instance stops. "
            "PostgreSQL row-level security is not claimed."
        )
    return (
        "SQLite with application-enforced account separation. "
        "PostgreSQL row-level security is not claimed: no PostgreSQL server is configured."
    )


def data_root() -> Path:
    if os.environ.get("VERCEL", "").strip() == "1" and not os.environ.get("RETRACE_DATA"):
        return Path("/tmp/retrace")
    return Path(os.environ.get("RETRACE_DATA", "data"))


def client_key(request: Request) -> str:
    return request.client.host if request.client else "local"


def take_limit(request: Request, bucket_name: str, maximum: int) -> JSONResponse | None:
    now = time.monotonic()
    key = f"{bucket_name}:{client_key(request)}"
    bucket = [stamp for stamp in _HITS.get(key, []) if now - stamp < 60]
    if len(bucket) >= maximum:
        return JSONResponse(
            {
                "error": "rate_limited",
                "message": "Too many requests from this machine.",
                "next": "Wait a minute and try again.",
            },
            status_code=429,
        )
    bucket.append(now)
    _HITS[key] = bucket
    return None


def apply_public_headers(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


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
        "profile": "public-scientist",
        "release_decision": "REVISE",
        "sandbox": "Curated demonstration notebooks only. No tested sandbox is configured, so other notebooks are refused.",
        "database": database_description(),
        "database_mode": database_mode(),
        "models": {
            "anthropic": model_state("ANTHROPIC_API_KEY"),
            "openrouter": model_state("OPENROUTER_API_KEY"),
            "repairs": "deterministic-diagnoser",
            "note": "Repairs stay with the deterministic diagnoser. This API process does not call a model. The desk conversation calls OpenRouter only when OPENROUTER_API_KEY is set on the desk server. Notebooks and stored results are not included.",
        },
        "connectors": connector_rows(),
    }


def create_app(database: Path, objects: Path, database_url: str | None = None) -> FastAPI:
    service = Service(Store(database, objects, database_url=database_url))
    app = FastAPI(title="RETRACE", version=__version__, docs_url=None, redoc_url=None)
    app.state.service = service
    app.state.engine = service.store.engine
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(allowed_origins()),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Origin"],
    )

    @app.middleware("http")
    async def platform_guard(request: Request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            bucket = "sign-in" if request.url.path == "/api/session" and request.method == "POST" else "change"
            maximum = _SIGN_IN_LIMIT if bucket == "sign-in" else _CHANGE_LIMIT
            blocked = take_limit(request, bucket, maximum)
            if blocked is not None:
                return apply_public_headers(blocked)
        response = await call_next(request)
        return apply_public_headers(response)

    @app.exception_handler(RetraceError)
    async def on_error(_request: Request, exc: RetraceError) -> JSONResponse:
        return JSONResponse(exc.as_dict(), status_code=exc.status)

    def principal(request: Request) -> dict:
        found = service.principal_from_token(request.cookies.get("retrace_session"))
        if found is None:
            raise RetraceError(
                "sign_in_required",
                "Sign in before opening a project.",
                "Enter the name you use on this platform.",
                status=401,
            )
        return found

    def guard(request: Request) -> None:
        if request.method == "GET":
            return
        origin = request.headers.get("origin")
        if origin not in allowed_origins():
            raise RetraceError(
                "origin_rejected",
                "The request origin is not allowed to change records on this service.",
                "Open RETRACE from the address the operator published.",
                status=403,
            )

    def set_session(response: Response, token: str) -> None:
        response.set_cookie(
            "retrace_session",
            token,
            httponly=True,
            samesite="lax",
            secure=cookie_secure(),
            path="/",
            max_age=60 * 60 * 12,
        )

    def clear_session(response: Response) -> None:
        response.delete_cookie("retrace_session", path="/", httponly=True, samesite="lax", secure=cookie_secure())

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True, "product": "RETRACE", "version": __version__}

    @app.get("/api/privacy")
    def privacy() -> dict:
        return privacy_notice()

    @app.get("/api/capabilities")
    def caps() -> dict:
        return capabilities()

    @app.get("/api/locales")
    def locale_list() -> dict:
        rows = locales()
        return {
            "locales": rows,
            "shipped_interface_locale": "en",
            "note": "English is the authored source language. Other locales are interface drafts and have not had linguistic review. Arabic, Hebrew, Persian, and Urdu are right to left. Project names, notebooks, and scientific records stay in their source language.",
        }

    def slack_token_for(request: Request) -> str | None:
        person = service.principal_from_token(request.cookies.get("retrace_session"))
        if person is None:
            return None
        saved = service.store.connector_secret(person["id"], "slack")
        return saved[0] if saved else ""

    @app.get("/api/connectors")
    def connectors(request: Request) -> dict:
        person = service.principal_from_token(request.cookies.get("retrace_session"))
        if person is not None:
            service.ensure_mcp_client(person)
        return {"connectors": connector_rows(slack_token_for(request))}

    @app.post("/api/connectors/github/export")
    def github_export(request: Request, payload: dict) -> dict:
        guard(request)
        person = principal(request)
        login = github_login()
        if login is None:
            raise RetraceError(
                "github_signed_out",
                "No GitHub account is signed in on this computer.",
                "Sign in with the GitHub command on this machine, then try the export again.",
                status=409,
            )
        pack = service.share_notebook(person, str(payload.get("project_id") or ""))
        files = github_files(
            pack["project_id"],
            notebook_filename(pack["notebook_path"]),
            pack["title"],
            pack["question"],
            pack["notebook"],
        )
        return export_github(
            login=login,
            repository=str(payload.get("repository") or ""),
            create=bool(payload.get("create")),
            files=files,
        )

    @app.post("/api/connectors/slack")
    def slack_connect(request: Request, payload: dict) -> dict:
        guard(request)
        person = principal(request)
        token = clean_slack_token(str(payload.get("token") or ""))
        found = probe_slack(token)
        if found is None:
            raise RetraceError(
                "bad_slack_token",
                "Slack did not accept that token.",
                "Check the token from your own workspace. It was not saved.",
            )
        service.store.save_connector_secret(person["id"], "slack", token, found["team"])
        row = slack_connector(token)
        if token in json.dumps(row):
            raise RetraceError("slack_refused", "The workspace connection could not be saved.", "Try the token again.", status=500)
        return row

    @app.post("/api/connectors/slack/disconnect")
    def slack_disconnect(request: Request) -> dict:
        guard(request)
        person = principal(request)
        service.store.clear_connector_secret(person["id"], "slack")
        return slack_connector("")

    @app.post("/api/connectors/slack/share")
    def slack_share(request: Request, payload: dict) -> dict:
        guard(request)
        person = principal(request)
        saved = service.store.connector_secret(person["id"], "slack")
        if saved is None:
            raise RetraceError(
                "slack_signed_out",
                "Connect your Slack workspace before sharing.",
                "Paste a token from your own Slack app.",
                status=409,
            )
        token, _label = saved
        channel = clean_channel(str(payload.get("channel") or ""))
        pack = service.share_notebook(person, str(payload.get("project_id") or ""))
        post_slack(token, channel, slack_text(pack["title"], pack["question"]))
        return {
            "message": f"Shared {pack['title']} to {channel}.",
            "next": "The message is the project title and question. The notebook was not sent, and this is not a reproduction result.",
        }

    @app.get("/api/projects/{project_id}/notebook")
    def project_notebook(request: Request, project_id: str) -> Response:
        pack = service.share_notebook(principal(request), project_id)
        filename = notebook_filename(pack["notebook_path"])
        return Response(
            pack["notebook"].encode("utf-8"),
            media_type="application/x-ipynb+json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/mcp")
    async def mcp(request: Request) -> Response:
        try:
            message = await request.json()
        except json.JSONDecodeError:
            return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}, status_code=400)
        if not isinstance(message, dict):
            return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}, status_code=400)
        header = request.headers.get("authorization") or ""
        bearer = header[7:].strip() if header.lower().startswith("bearer ") else ""
        person = service.principal_from_mcp_key(bearer) if bearer else service.principal_from_token(request.cookies.get("retrace_session"))
        if person is None:
            result = handle_mcp(message)
        else:
            result = handle_mcp(
                message,
                account=person,
                read_projects=lambda: service.mcp_projects(person),
                read_project=lambda project_id: service.mcp_project(person, project_id),
            )
        if result is None:
            return Response(status_code=202)
        return JSONResponse(result)

    @app.get("/api/ui-plan/catalogue")
    def ui_catalogue() -> dict:
        return catalogue()

    @app.post("/api/session")
    def sign_in(request: Request, payload: dict) -> JSONResponse:
        guard(request)
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
        clear_session(response)
        return response

    @app.get("/api/account/export")
    def export_account(request: Request) -> JSONResponse:
        body = service.export_account(principal(request))
        response = JSONResponse(body)
        response.headers["Content-Disposition"] = 'attachment; filename="retrace-record.json"'
        return response

    @app.delete("/api/account")
    def erase_account(request: Request) -> Response:
        guard(request)
        service.erase_account(principal(request))
        response = Response(status_code=204)
        clear_session(response)
        return response

    @app.get("/api/preferences")
    def get_preferences(request: Request) -> dict:
        found = service.principal_from_token(request.cookies.get("retrace_session"))
        if found is None:
            return {"theme": "system", "density": "comfortable", "zone": "UTC", "locale": "en", "signed_in": False}
        saved = service.preferences(found)
        saved["signed_in"] = True
        return saved

    @app.put("/api/preferences")
    def put_preferences(request: Request, payload: dict) -> dict:
        guard(request)
        raw_locale = payload.get("locale")
        return service.save_preferences(
            principal(request),
            str(payload.get("theme", "system")),
            str(payload.get("density", "comfortable")),
            str(payload.get("zone", "UTC")),
            None if raw_locale is None else str(raw_locale),
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
    root = data_root()
    root.mkdir(parents=True, exist_ok=True)
    return create_app(root / "retrace.sqlite", root / "objects", database_url())


def main() -> None:
    import uvicorn

    uvicorn.run(default_app(), host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
