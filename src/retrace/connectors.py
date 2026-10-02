"""Workstation connections for the signed-in person's own accounts.

A connector is OPERATIONAL only after a check on this machine succeeds.
Missing credentials stay NEEDS_CONFIGURATION. Export goes to a repository
that account can write. The RETRACE application repository is refused.
Colab is never an execution backend: this module does not run a notebook.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from typing import Any, Callable

from retrace import __version__
from retrace.errors import RetraceError

_APP_REPOSITORY = "frankasantevanlaarhoven/retraceos"
_LOGIN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
_REPO_NAME = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
_NOTEBOOK = re.compile(r"^[A-Za-z0-9._-]{1,80}\.ipynb$")
_PROJECT = re.compile(r"^[a-f0-9]{32}$")
_CHANNEL = re.compile(r"[A-Za-z0-9_-]{1,80}")
_GITHUB_CACHE: dict[str, Any] = {"at": 0.0, "row": None}
_SLACK_CACHE: dict[str, Any] = {"at": 0.0, "row": None}
_SLACK_TOKEN_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}

Runner = Callable[..., Any]


def _row(
    connector_id: str,
    status: str,
    detail: str,
    actions: list[dict[str, str]] | None = None,
    account: str | None = None,
) -> dict[str, Any]:
    return {
        "id": connector_id,
        "status": status,
        "detail": detail,
        "actions": actions or [],
        "account": account,
    }


def _needs(connector_id: str, detail: str, actions: list[dict[str, str]] | None = None, account: str | None = None) -> dict[str, Any]:
    return _row(connector_id, "NEEDS_CONFIGURATION", detail, actions, account)


def _working(connector_id: str, detail: str, actions: list[dict[str, str]] | None = None, account: str | None = None) -> dict[str, Any]:
    return _row(connector_id, "OPERATIONAL", detail, actions, account)


def _run(args: list[str], input_text: str | None = None, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, input=input_text, check=False, capture_output=True, text=True, timeout=timeout)


def _safe_text(value: str) -> str:
    cleaned = " ".join((value or "").split())[:180]
    if any(mark in cleaned for mark in ("ghp_", "github_pat_", "xox", "Bearer ")):
        return "The service refused the request."
    return cleaned or "The service refused the request."


def github_login(run: Runner | None = None) -> str | None:
    """Return the GitHub login signed in on this computer, or None."""
    runner = _run if run is None else run
    try:
        result = runner(["gh", "api", "user", "--jq", ".login"], input_text=None, timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        return None
    login = (getattr(result, "stdout", "") or "").strip()
    if getattr(result, "returncode", 1) != 0 or not login or any(char.isspace() for char in login):
        return None
    if not _LOGIN.fullmatch(login):
        return None
    return login


def github_connector(now: float | None = None) -> dict[str, Any]:
    moment = time.monotonic() if now is None else now
    cached = _GITHUB_CACHE["row"]
    if cached is not None and moment - float(_GITHUB_CACHE["at"]) < 30:
        return cached
    login = github_login()
    if login is None:
        row = _needs(
            "github",
            "No GitHub account is signed in on this computer. Sign in with the GitHub command on this machine, then choose Check again. Nothing is exported until you do.",
        )
    else:
        row = _working(
            "github",
            f"Signed in on this computer as {login}. Export a project to a repository this account can write. The RETRACE application repository is not used.",
            [{"href": f"https://github.com/{login}", "label": "Open your GitHub"}],
            account=login,
        )
    _GITHUB_CACHE["at"] = moment
    _GITHUB_CACHE["row"] = row
    return row


def notebook_filename(path: str) -> str:
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    return name if _NOTEBOOK.fullmatch(name) else "notebook.ipynb"


def github_files(project_id: str, filename: str, title: str, question: str, notebook: str) -> dict[str, str]:
    if not _PROJECT.fullmatch(project_id) or not _NOTEBOOK.fullmatch(filename):
        raise RetraceError("not_found", "That project is not on this account.", "Open a project from your desk.", status=404)
    if not notebook.strip():
        raise RetraceError("no_notebook", "This project has no notebook to export.", "Open a project that has a notebook.", status=409)
    heading = " ".join(title.split())[:160] or "Project"
    asked = question.strip()[:2000]
    readme = (
        f"# {heading}\n\n"
        "Exported from a local RETRACE desk so this project can be shared.\n\n"
        "This is a copy of the notebook stored on that desk. "
        "Opening it on GitHub or in Colab does not rerun it, and it is not a reproduction result.\n\n"
        f"Project question as stored:\n\n{asked}\n"
    )
    folder = f"retrace/{project_id}"
    return {f"{folder}/README.md": readme, f"{folder}/{filename}": notebook}


def _split_repository(repository: str) -> tuple[str, str]:
    parts = repository.strip().split("/")
    if len(parts) != 2 or not _LOGIN.fullmatch(parts[0]) or not _REPO_NAME.fullmatch(parts[1]):
        raise RetraceError(
            "bad_repository",
            "Type the repository as the account name, a slash, and the repository name.",
            "Use a repository on your own GitHub account, such as your-name/your-notes.",
        )
    if f"{parts[0]}/{parts[1]}".lower() == _APP_REPOSITORY:
        raise RetraceError(
            "app_repository",
            "That repository is the RETRACE application, not a place for your project.",
            "Type a repository on your own account.",
        )
    return parts[0], parts[1]


def _api(runner: Runner, path: str, method: str | None = None, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any] | None, str]:
    args = ["gh", "api"]
    if method:
        args.extend(["--method", method])
    args.append(path)
    input_text = json.dumps(payload) if payload is not None else None
    if payload is not None:
        args.extend(["--input", "-"])
    try:
        result = runner(args, input_text=input_text, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RetraceError(
            "github_unavailable",
            "GitHub could not be reached from this computer.",
            "Check the GitHub sign-in on this machine and try the export again.",
            status=502,
        ) from exc
    code = int(getattr(result, "returncode", 1))
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    if code != 0:
        return code, None, _safe_text(stderr or stdout)
    try:
        body = json.loads(stdout or "null")
    except json.JSONDecodeError:
        return 0, None, ""
    return 0, body if isinstance(body, dict) else None, ""


def export_github(
    *,
    login: str,
    repository: str,
    create: bool,
    files: dict[str, str],
    run: Runner | None = None,
) -> dict[str, str]:
    """Upload share files to a repository the signed-in account can write."""
    if not _LOGIN.fullmatch(login):
        raise RetraceError(
            "github_signed_out",
            "No GitHub account is signed in on this computer.",
            "Sign in with the GitHub command on this machine, then try the export again.",
            status=409,
        )
    owner, name = _split_repository(repository)
    runner = _run if run is None else run
    code, body, err = _api(runner, f"repos/{owner}/{name}")
    if code != 0 or body is None:
        if not create:
            raise RetraceError(
                "repository_unavailable",
                "That repository is not available to the signed-in GitHub account.",
                "Choose a repository you can write, or tick the box to create a private one under your account.",
                status=404,
            )
        if owner.lower() != login.lower():
            raise RetraceError(
                "repository_unavailable",
                "A new repository can only be created under the GitHub account signed in on this computer.",
                f"Use {login}/your-notes, or choose a repository that account can already write.",
                status=404,
            )
        try:
            created = runner(
                [
                    "gh",
                    "repo",
                    "create",
                    f"{owner}/{name}",
                    "--private",
                    "--description",
                    "Project exported from a local RETRACE desk for sharing.",
                ],
                input_text=None,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RetraceError(
                "github_unavailable",
                "GitHub could not be reached from this computer.",
                "Check the GitHub sign-in on this machine and try the export again.",
                status=502,
            ) from exc
        if int(getattr(created, "returncode", 1)) != 0:
            raise RetraceError(
                "repository_unavailable",
                "GitHub did not create that private repository.",
                _safe_text(getattr(created, "stderr", "") or ""),
                status=502,
            )
        code, body, err = _api(runner, f"repos/{owner}/{name}")
        if code != 0 or body is None:
            raise RetraceError(
                "repository_unavailable",
                "The private repository was not readable after it was created.",
                "Open your GitHub account and check the new repository, then export again.",
                status=502,
            )
    full_name = str(body.get("full_name") or "")
    if full_name.lower() != f"{owner}/{name}".lower() or "/" not in full_name:
        raise RetraceError(
            "repository_unavailable",
            "GitHub returned a different repository from the one you typed.",
            "Type the repository again.",
            status=409,
        )
    if full_name.lower() == _APP_REPOSITORY:
        raise RetraceError(
            "app_repository",
            "That repository is the RETRACE application, not a place for your project.",
            "Type a repository on your own account.",
        )
    owner, name = full_name.split("/", 1)
    permissions = body.get("permissions") if isinstance(body.get("permissions"), dict) else {}
    if permissions.get("push") is not True:
        raise RetraceError(
            "cannot_write",
            "This GitHub account cannot write to that repository.",
            "Choose a repository you can write, or create a private one under your account.",
            status=403,
        )
    branch = str(body.get("default_branch") or "main")
    if not re.fullmatch(r"[A-Za-z0-9._/-]{1,120}", branch):
        branch = "main"
    branch_code, _, _ = _api(runner, f"repos/{owner}/{name}/branches/{urllib.parse.quote(branch, safe='')}")
    has_branch = branch_code == 0
    for path, text in files.items():
        if not path.startswith("retrace/") or ".." in path.split("/"):
            raise RetraceError("bad_export", "The export path is not allowed.", "Export the project again from this desk.", status=400)
        payload: dict[str, Any] = {
            "message": "Export a project from RETRACE for sharing",
            "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        }
        if has_branch:
            encoded = urllib.parse.quote(path, safe="")
            existing_code, existing, existing_err = _api(
                runner,
                f"repos/{owner}/{name}/contents/{encoded}?ref={urllib.parse.quote(branch, safe='')}",
            )
            if existing_code != 0 and "404" not in existing_err and "Not Found" not in existing_err:
                raise RetraceError(
                    "github_unavailable",
                    "GitHub did not accept the export.",
                    existing_err,
                    status=502,
                )
            if existing_code == 0 and existing and existing.get("sha"):
                payload["sha"] = str(existing["sha"])
            payload["branch"] = branch
        put_code, _, put_err = _api(
            runner,
            f"repos/{owner}/{name}/contents/{urllib.parse.quote(path, safe='')}",
            method="PUT",
            payload=payload,
        )
        if put_code != 0:
            raise RetraceError("github_unavailable", "GitHub did not accept the export.", put_err, status=502)
        has_branch = True
    notebook_path = next(path for path in files if path.endswith(".ipynb"))
    blob = f"https://github.com/{owner}/{name}/blob/{branch}/{notebook_path}"
    return {
        "repository": f"{owner}/{name}",
        "url": f"https://github.com/{owner}/{name}",
        "notebook_url": blob,
        "colab_url": f"https://colab.research.google.com/github/{owner}/{name}/blob/{branch}/{notebook_path}",
        "message": f"Exported to {owner}/{name}.",
        "next": "Open the repository to share it. If it is private, sign in to Colab with this GitHub account before opening the notebook there. This export does not rerun the notebook.",
    }


def probe_slack(token: str) -> dict[str, str] | None:
    request = urllib.request.Request(
        "https://slack.com/api/auth.test",
        data=b"",
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError, TimeoutError):
        return None
    if not body.get("ok"):
        return None
    team = str(body.get("team") or "").strip()
    return {"team": team} if team else None


def clean_slack_token(value: str) -> str:
    token = value.strip()
    if not 10 <= len(token) <= 200 or any(char.isspace() for char in token) or not token.startswith(("xoxb-", "xoxp-")):
        raise RetraceError(
            "bad_slack_token",
            "That does not look like a Slack token for your workspace.",
            "Paste the bot or user token from your own Slack app. It was not saved.",
        )
    return token


def clean_channel(value: str) -> str:
    channel = value.strip()
    if channel.startswith("#"):
        channel = channel[1:]
    if not _CHANNEL.fullmatch(channel):
        raise RetraceError(
            "bad_channel",
            "Type the channel name from your workspace.",
            "Use letters, numbers, hyphens, or underscores.",
        )
    return channel


def slack_text(title: str, question: str) -> str:
    heading = " ".join(title.split())[:160] or "Project"
    asked = " ".join(question.split())[:500]
    return (
        f"{heading}\n{asked}\n"
        "Shared from a local RETRACE desk. This note is the project title and question. "
        "The notebook was not sent, and this is not a reproduction result."
    )


def post_slack(token: str, channel: str, text: str) -> None:
    payload = json.dumps({"channel": channel, "text": text}).encode("utf-8")
    request = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError, TimeoutError) as exc:
        raise RetraceError(
            "slack_unavailable",
            "Slack could not be reached from this computer.",
            "Check the workspace connection and try again. Nothing else was sent.",
            status=502,
        ) from exc
    if body.get("ok"):
        return
    code = str(body.get("error") or "")
    if code == "not_in_channel":
        raise RetraceError(
            "slack_channel",
            "Slack did not post, because the app is not in that channel.",
            "Invite the app to the channel, then share again.",
            status=409,
        )
    if code == "channel_not_found":
        raise RetraceError(
            "slack_channel",
            "Slack could not find that channel.",
            "Check the channel name in your workspace.",
            status=404,
        )
    raise RetraceError(
        "slack_refused",
        "Slack did not post the message.",
        "Check the channel and the workspace token. Nothing else was sent.",
        status=502,
    )


def slack_connector(token: str | None = None, now: float | None = None) -> dict[str, Any]:
    """token None uses the workstation environment. An empty token is not connected."""
    moment = time.monotonic() if now is None else now
    if token is None:
        cached = _SLACK_CACHE["row"]
        if cached is not None and moment - float(_SLACK_CACHE["at"]) < 30:
            return cached
        token = os.environ.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_TOKEN") or ""
        found = probe_slack(token) if token else None
        row = _slack_row(found)
        _SLACK_CACHE["at"] = moment
        _SLACK_CACHE["row"] = row
        return row
    if not token:
        return _slack_row(None)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    cached_token = _SLACK_TOKEN_CACHE.get(digest)
    if cached_token is not None and moment - cached_token[0] < 30:
        return cached_token[1]
    row = _slack_row(probe_slack(token))
    _SLACK_TOKEN_CACHE[digest] = (moment, row)
    return row


def _slack_row(found: dict[str, str] | None) -> dict[str, Any]:
    if found is None:
        return _needs(
            "slack",
            "Connect the Slack workspace where you want to share a project. Nothing is sent to Slack until you do.",
        )
    return _working(
        "slack",
        f"Connected to the Slack workspace {found['team']}. Share a project title and question into a channel this installation can post in. The notebook is not sent.",
        account=found["team"],
    )


def google_calendar_connector() -> dict[str, Any]:
    client_id = os.environ.get("GOOGLE_CALENDAR_CLIENT_ID") or os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    detail = (
        "This workstation has not signed in to Google, so it does not write into a Google account. "
        "Download the calendar file and import it into your own Google Calendar."
    )
    if client_id:
        detail = (
            "A Google client id is present, but this desk has not completed a calendar sign-in. "
            "Download the calendar file and import it into your own Google Calendar."
        )
    return _needs(
        "google_calendar",
        detail,
        [
            {"href": "/calendar", "label": "Open the desk calendar"},
            {"href": "/api/calendar.ics", "label": "Download the calendar file"},
            {"href": "https://calendar.google.com/calendar/r", "label": "Open your Google Calendar"},
        ],
    )


def colab_connector() -> dict[str, Any]:
    return _needs(
        "colab",
        "Download a project notebook and open it in your own Colab account. Notebooks are not sent to Colab. This desk does not sign in to Colab and does not run the notebook there.",
        [{"href": "https://colab.research.google.com/", "label": "Open Colab"}],
    )


def mcp_connector() -> dict[str, Any]:
    row = _working(
        "mcp",
        "Tools on this computer can read your project names and questions, and which of your accounts are connected. They cannot run a notebook or send the work anywhere.",
    )
    row["notes"] = [
        "Read whether this desk is running",
        "Read which of your accounts are connected",
        "Read the name and question of each of your projects",
    ]
    return row


def connector_rows(slack_token: str | None = None) -> list[dict[str, Any]]:
    return [
        github_connector(),
        slack_connector(slack_token),
        google_calendar_connector(),
        colab_connector(),
        mcp_connector(),
    ]


_TOOLS = [
    {
        "name": "retrace_health",
        "description": "Report whether the local RETRACE service is up. This does not run a notebook.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "retrace_connectors",
        "description": "List connector states on this workstation. This does not run a notebook or call a model.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "retrace_projects",
        "description": "List the signed-in person's projects by name and question. This does not run a notebook.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "retrace_project",
        "description": "Read one project that belongs to the signed-in person. This does not run a notebook or make a reproduction claim.",
        "inputSchema": {
            "type": "object",
            "properties": {"project_id": {"type": "string"}},
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
]


def handle_mcp(
    message: dict[str, Any],
    *,
    account: dict[str, Any] | None = None,
    read_projects: Callable[[], list[dict[str, Any]]] | None = None,
    read_project: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    method = str(message.get("method") or "")
    msg_id = message.get("id")
    if msg_id is None or method.startswith("notifications/"):
        return None

    def ok(result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    if method == "initialize":
        return ok(
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "RETRACE", "version": __version__},
            }
        )
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": _TOOLS})
    if method == "tools/call":
        name = str((message.get("params") or {}).get("name") or "")
        if name == "retrace_health":
            text = json.dumps({"ok": True, "product": "RETRACE", "version": __version__})
            return ok({"content": [{"type": "text", "text": text}], "isError": False})
        if name == "retrace_connectors":
            brief = [{"id": row["id"], "status": row["status"]} for row in connector_rows()]
            return ok({"content": [{"type": "text", "text": json.dumps(brief)}], "isError": False})
        if name in {"retrace_projects", "retrace_project"}:
            if account is None or read_projects is None or read_project is None:
                return ok(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": "This tool reads projects for one desk account. Connect the tool as that person. No project was read.",
                            }
                        ],
                        "isError": True,
                    }
                )
            try:
                if name == "retrace_projects":
                    body: Any = read_projects()
                else:
                    project_id = str(((message.get("params") or {}).get("arguments") or {}).get("project_id") or "")
                    body = read_project(project_id)
            except RetraceError as exc:
                return ok({"content": [{"type": "text", "text": exc.message}], "isError": True})
            return ok({"content": [{"type": "text", "text": json.dumps(body)}], "isError": False})
        return ok(
            {
                "content": [
                    {
                        "type": "text",
                        "text": "That tool is not available. This connection cannot run a notebook or send work to Colab.",
                    }
                ],
                "isError": True,
            }
        )
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}}
