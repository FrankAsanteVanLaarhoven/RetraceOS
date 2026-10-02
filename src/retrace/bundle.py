from __future__ import annotations

import io
import json
import zipfile
from typing import Any

from retrace.errors import RetraceError
from retrace.hashing import sha256_bytes

_LIMIT_BYTES = 8_000_000
_LIMIT_FILES = 40


def _member_name(name: str) -> str:
    if name.startswith("/") or "\\" in name or ".." in name.split("/"):
        raise RetraceError(
            "unsafe_bundle",
            "The evidence bundle contains an unsafe path.",
            "Export the bundle again from RETRACE. Do not repackage it by hand.",
        )
    return name


def build_bundle(document: dict[str, Any], files: dict[str, bytes]) -> bytes:
    """A portable subset of a Workflow Run RO-Crate.

    Content hashes are inside the crate. This is not a claim that the bundle
    passes a full RO-Crate profile validator.
    """

    file_entries = []
    for path in sorted(files):
        _member_name(path)
        file_entries.append(
            {
                "@id": path,
                "@type": "File",
                "sha256": sha256_bytes(files[path]),
                "contentSize": len(files[path]),
            }
        )
    graph = [
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            "about": {"@id": "./"},
        },
        {
            "@id": "./",
            "@type": "Dataset",
            "name": document["title"],
            "description": (
                "RETRACE evidence bundle. Structure follows a Workflow Run RO-Crate subset. "
                "It has not been certified against the full profile."
            ),
            "dateCreated": document["created_at"],
        },
        {
            "@id": "#run",
            "@type": "CreateAction",
            "name": "Isolated notebook rerun",
            "instrument": {"@id": "analysis.ipynb"},
            "result": {"@id": "outputs/results.json"},
        },
        {
            "@id": "#verification",
            "@type": "CreateAction",
            "name": "Independent result-contract comparison",
            "object": {"@id": "contract.json"},
            "result": {"@id": "verification.json"},
        },
    ]
    graph.extend(file_entries)
    crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": graph,
        "retrace": document,
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ro-crate-metadata.json", json.dumps(crate, indent=2, sort_keys=True))
        for path, data in sorted(files.items()):
            archive.writestr(path, data)
    return buffer.getvalue()


def read_bundle(payload: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    if len(payload) > _LIMIT_BYTES:
        raise RetraceError(
            "bundle_too_large",
            "The evidence bundle is larger than this workstation profile accepts.",
            "Import a bundle exported from a demonstration project.",
            status=413,
        )
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        raise RetraceError(
            "bad_bundle",
            "The file is not a readable evidence bundle.",
            "Choose a .zip exported from RETRACE.",
        ) from exc
    names = archive.namelist()
    if len(names) > _LIMIT_FILES:
        raise RetraceError(
            "bundle_too_large",
            "The bundle contains more files than this profile accepts.",
            "Import a demonstration bundle.",
        )
    if "ro-crate-metadata.json" not in names:
        raise RetraceError(
            "bad_bundle",
            "The bundle has no ro-crate-metadata.json.",
            "Export the bundle again from the evidence stage.",
        )
    files: dict[str, bytes] = {}
    for info in archive.infolist():
        name = _member_name(info.filename)
        if name.endswith("/"):
            continue
        if info.file_size > 2_000_000:
            raise RetraceError(
                "bundle_too_large",
                f"{name} exceeds the file size limit.",
                "Import a demonstration bundle.",
            )
        files[name] = archive.read(info)
    try:
        crate = json.loads(files.pop("ro-crate-metadata.json").decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RetraceError(
            "bad_bundle",
            "The crate metadata is not readable JSON.",
            "Export the bundle again.",
        ) from exc
    claimed = {entry["@id"]: entry.get("sha256") for entry in crate.get("@graph", []) if entry.get("@type") == "File"}
    for path, data in files.items():
        expected = claimed.get(path)
        actual = sha256_bytes(data)
        if expected != actual:
            raise RetraceError(
                "tampered_bundle",
                f"The hash of {path} does not match the crate.",
                "Do not use this bundle as evidence. Export it again from the original run.",
                status=422,
            )
    document = crate.get("retrace")
    if not isinstance(document, dict):
        raise RetraceError(
            "bad_bundle",
            "The crate does not contain a RETRACE evidence record.",
            "Export the bundle from the evidence stage.",
        )
    return document, files
