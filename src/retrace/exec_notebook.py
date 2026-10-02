"""Run one admitted notebook inside a prepared workspace.

The parent process chooses the workspace, the environment, and the time limit.
This module does not see the result contract and cannot write a verification status.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: python -m retrace.exec_notebook WORKSPACE NOTEBOOK", file=sys.stderr)
        return 2
    workspace = Path(args[0]).resolve()
    notebook_path = (workspace / args[1]).resolve()
    if notebook_path.parent != workspace and workspace not in notebook_path.parents:
        print("Notebook path escapes the workspace.", file=sys.stderr)
        return 2
    if not str(notebook_path).startswith(str(workspace)):
        print("Notebook path escapes the workspace.", file=sys.stderr)
        return 2

    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (20, 25))
        resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
    except (ImportError, ValueError, OSError):
        pass

    os.chdir(workspace)
    import nbformat
    from nbclient import NotebookClient

    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=20,
        kernel_name="retrace",
        resources={"metadata": {"path": str(workspace)}},
    )
    try:
        client.execute()
    except Exception as exc:  # noqa: BLE001 — surface the notebook failure to the parent log
        print(f"RETRACE_EXEC_FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
