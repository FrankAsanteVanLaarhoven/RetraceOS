from __future__ import annotations

import nbformat

from retrace.errors import RetraceError


def code_cells(notebook_bytes: bytes) -> list[str]:
    notebook = nbformat.reads(notebook_bytes.decode("utf-8"), as_version=4)
    return [cell.source for cell in notebook.cells if cell.cell_type == "code"]


def joined_code(notebook_bytes: bytes) -> str:
    return "\n".join(code_cells(notebook_bytes))


def apply_notebook_edit(notebook_bytes: bytes, find: str, replace: str) -> bytes:
    if not find:
        raise RetraceError(
            "empty_find",
            "The repair does not identify the text it replaces.",
            "Include the exact notebook text the repair will change.",
        )
    notebook = nbformat.reads(notebook_bytes.decode("utf-8"), as_version=4)
    hits: list[int] = []
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code" and find in cell.source:
            hits.append(index)
    if len(hits) != 1 or notebook.cells[hits[0]].source.count(find) != 1:
        count = sum(cell.source.count(find) for cell in notebook.cells if cell.cell_type == "code")
        raise RetraceError(
            "patch_not_unique",
            f"The repair text matched {count} places in the notebook. It must match once.",
            "Narrow the repair to the single passage it is meant to change.",
        )
    cell = notebook.cells[hits[0]]
    cell.source = cell.source.replace(find, replace, 1)
    return nbformat.writes(notebook).encode("utf-8")
