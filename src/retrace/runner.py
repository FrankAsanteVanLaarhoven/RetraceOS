from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from retrace.errors import RetraceError

_KEEP = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "SYSTEMROOT", "WINDIR")
_SECRET_HINTS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "COOKIE")


@dataclass
class Execution:
    status: str
    results: dict | None
    malformed_output: bool
    log: str


def _child_env(workspace: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for key in _KEEP:
        if key in os.environ and not any(hint in key for hint in _SECRET_HINTS):
            env[key] = os.environ[key]
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        env["VIRTUAL_ENV"] = venv
        env["PATH"] = str(Path(venv) / "bin") + os.pathsep + env.get("PATH", "")
    env["HOME"] = str(workspace)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MPLBACKEND"] = "Agg"
    return env


def _read_results(workspace: Path) -> tuple[dict | None, bool]:
    path = workspace / "outputs" / "results.json"
    if path.is_symlink():
        raise RetraceError(
            "unsafe_output",
            "The notebook result is a symlink. RETRACE did not follow it.",
            "Write a regular outputs/results.json file inside the workspace.",
        )
    if not path.is_file():
        return None, False
    if path.stat().st_size > 65_536:
        return None, True
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, True
    if not isinstance(payload, dict):
        return None, True
    return payload, False


def execute_workspace(files: dict[str, bytes], notebook_path: str) -> Execution:
    """Execute an already materialised candidate. Caller must have applied the allowlist."""

    if notebook_path not in files:
        raise RetraceError(
            "missing_notebook",
            "The snapshot does not contain the notebook that was approved.",
            "Import the notebook again and review a new repair.",
        )
    workspace = Path(tempfile.mkdtemp(prefix="retrace-run-"))
    try:
        root = workspace.resolve()
        for relative, data in files.items():
            parts = Path(relative).parts
            if not relative or relative.startswith("/") or "\\" in relative or ".." in parts:
                raise RetraceError(
                    "unsafe_path",
                    "A snapshot path escapes the run workspace.",
                    "Reject the package and import a flat notebook and data directory.",
                )
            destination = (workspace / relative).resolve()
            if not destination.is_relative_to(root):
                raise RetraceError(
                    "unsafe_path",
                    "A snapshot path escapes the run workspace.",
                    "Reject the package and import a flat notebook and data directory.",
                )
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        completed = subprocess.run(
            [sys.executable, "-m", "retrace.exec_notebook", str(workspace), notebook_path],
            cwd=workspace,
            env=_child_env(workspace),
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        log = (completed.stdout + "\n" + completed.stderr).strip()[:16_000]
        if completed.returncode != 0:
            return Execution("FAILED", None, False, log or "The notebook process failed.")
        results, malformed = _read_results(workspace)
        return Execution("SUCCEEDED", results, malformed, log)
    except subprocess.TimeoutExpired as exc:
        log = ""
        if exc.stderr:
            log = exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode("utf-8", "replace")
        return Execution("FAILED", None, False, (log or "The notebook exceeded the time limit.")[:16_000])
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
