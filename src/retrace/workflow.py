from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import nbformat
from sqlalchemy import select

from retrace.bundle import build_bundle, read_bundle
from retrace.classify import assert_label_allowed
from retrace.demo_fixtures import allowlist, cases
from retrace.errors import RetraceError
from retrace.hashing import sha256_bytes, sha256_json, snapshot_content_hash
from retrace.models import ResultContract
from retrace.notebook import apply_notebook_edit, joined_code
from retrace.runner import execute_workspace
from retrace.store import (
    Approval,
    CalendarEvent,
    ContractRow,
    Event,
    Layout,
    Preference,
    Principal,
    Project,
    Proposal,
    Run,
    SessionRow,
    Snapshot,
    SnapshotFile,
    Store,
    Tenant,
    WikiPage,
    as_utc,
    iso,
    utcnow,
)
from retrace.verifier import verify

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .'-]{0,39}$")
_ALLOWED_UPLOAD = {".ipynb", ".csv", ".tsv", ".txt", ".md", ".json"}


class Service:
    def __init__(self, store: Store) -> None:
        self.store = store

    def sign_in(self, display_name: str) -> tuple[dict, str]:
        name = " ".join(display_name.split())
        if not _NAME.match(name):
            raise RetraceError(
                "bad_name",
                "Use a display name of up to 40 letters, numbers, spaces, apostrophes, or hyphens.",
                "Enter the name colleagues should see on this workstation.",
            )
        now = utcnow()
        with self.store.session() as db:
            principal = db.scalar(select(Principal).where(Principal.display_name == name))
            if principal is None:
                tenant = Tenant(id=self.store.new_id(), created_at=now)
                principal = Principal(
                    id=self.store.new_id(),
                    tenant_id=tenant.id,
                    display_name=name,
                    created_at=now,
                )
                db.add(tenant)
                db.add(principal)
            token = secrets.token_urlsafe(32)
            db.add(
                SessionRow(
                    id=self.store.new_id(),
                    principal_id=principal.id,
                    token_hash=sha256_bytes(token.encode()),
                    expires_at=now + timedelta(hours=12),
                )
            )
            db.commit()
            return {"id": principal.id, "tenant_id": principal.tenant_id, "display_name": principal.display_name}, token

    def principal_from_token(self, token: str | None) -> dict | None:
        if not token:
            return None
        with self.store.session() as db:
            row = db.scalar(select(SessionRow).where(SessionRow.token_hash == sha256_bytes(token.encode())))
            if row is None or as_utc(row.expires_at) <= utcnow():
                return None
            principal = db.get(Principal, row.principal_id)
            if principal is None:
                return None
            return {"id": principal.id, "tenant_id": principal.tenant_id, "display_name": principal.display_name}

    def sign_out(self, token: str | None) -> None:
        if not token:
            return
        digest = sha256_bytes(token.encode())
        with self.store.session() as db:
            row = db.scalar(select(SessionRow).where(SessionRow.token_hash == digest))
            if row is not None:
                db.delete(row)
                db.commit()

    def preferences(self, principal: dict) -> dict:
        with self.store.session() as db:
            row = db.get(Preference, principal["id"])
            if row is None:
                return {"theme": "system", "density": "comfortable", "zone": "UTC"}
            return {"theme": row.theme, "density": row.density, "zone": row.zone}

    def save_preferences(self, principal: dict, theme: str, density: str, zone: str) -> dict:
        if theme not in {"light", "dark", "system"} or density not in {"comfortable", "compact"}:
            raise RetraceError("bad_preference", "Theme or density is not one of the available choices.", "Choose light, dark, or system, and comfortable or compact density.")
        try:
            ZoneInfo(zone)
        except ZoneInfoNotFoundError as exc:
            raise RetraceError("bad_zone", "That time zone is not a recognised IANA name.", "Choose a zone such as Europe/London or UTC.") from exc
        with self.store.session() as db:
            row = db.get(Preference, principal["id"])
            if row is None:
                row = Preference(principal_id=principal["id"], theme=theme, density=density, zone=zone)
                db.add(row)
            else:
                row.theme = theme
                row.density = density
                row.zone = zone
            db.commit()
        return self.preferences(principal)

    def list_projects(self, principal: dict) -> list[dict]:
        with self.store.session() as db:
            rows = db.scalars(
                select(Project)
                .where(Project.tenant_id == principal["tenant_id"], Project.retired_at.is_(None))
                .order_by(Project.created_at.desc())
            ).all()
            return [self._project_brief(row) for row in rows]

    def seed_demo(self, principal: dict, slug: str) -> dict:
        library = cases()
        if slug not in library:
            raise RetraceError("unknown_demo", "That demonstration is not in this build.", "Choose ecology, trajectory, or assay.", status=404)
        case = library[slug]
        self._reject_unsafe_tree(case.files)
        now = utcnow()
        with self.store.session() as db:
            project = Project(
                id=self.store.new_id(),
                tenant_id=principal["tenant_id"],
                name=case.title,
                discipline=case.discipline,
                question=case.question,
                demo_slug=slug,
                version=1,
                created_at=now,
            )
            db.add(project)
            snapshot = self._insert_snapshot(db, principal["tenant_id"], project.id, case.files, case.notebook_path, now)
            self._insert_contract(db, principal, project.id, case.contract, 1)
            self._insert_contract(db, principal, project.id, case.missing_contract, 2)
            self._insert_proposal(
                db,
                principal,
                project.id,
                snapshot,
                case.files,
                slug="diagnosed-path",
                title=case.diagnosis_title,
                claimed="execution_repair",
                author="deterministic-diagnoser",
                injected=False,
                rationale=case.diagnosis_rationale,
                find=case.diagnosis_find,
                replace=case.diagnosis_replace,
            )
            for trap in case.traps:
                self._insert_proposal(
                    db,
                    principal,
                    project.id,
                    snapshot,
                    case.files,
                    slug=trap.slug,
                    title=trap.title,
                    claimed="methodological_reanalysis",
                    author="demonstration-fixture",
                    injected=True,
                    rationale=trap.rationale,
                    find=trap.find,
                    replace=trap.replace,
                )
            self._event(db, principal, project.id, "imported", f"Admitted the {case.title} demonstration. Faults in it are injected.")
            db.commit()
            project_id = project.id
        return self.project_view(principal, project_id)

    def upload(self, principal: dict, name: str, files: dict[str, bytes]) -> dict:
        self._reject_unsafe_tree(files)
        notebooks = [path for path in files if path.endswith(".ipynb")]
        if len(notebooks) != 1:
            raise RetraceError(
                "notebook_required",
                "Import one notebook together with its tables.",
                "Choose a single .ipynb file and the CSV files it reads.",
            )
        now = utcnow()
        with self.store.session() as db:
            project = Project(
                id=self.store.new_id(),
                tenant_id=principal["tenant_id"],
                name=name[:160] or "Imported analysis",
                discipline="",
                question="",
                demo_slug=None,
                version=1,
                created_at=now,
            )
            db.add(project)
            self._insert_snapshot(db, principal["tenant_id"], project.id, files, notebooks[0], now)
            self._event(db, principal, project.id, "imported", "Imported a package. It can be inspected. It will not run unless it is an admitted demonstration.")
            db.commit()
            project_id = project.id
        return self.project_view(principal, project_id)

    def approve_contract(self, principal: dict, project_id: str, contract_id: str) -> dict:
        project = self._require_project(principal, project_id, writable=True)
        with self.store.session() as db:
            row = self._contract(db, principal["tenant_id"], contract_id)
            if row.project_id != project["id"]:
                raise RetraceError("not_found", "That contract is not in this project.", "Open the project and choose one of its contracts.", status=404)
            if row.status == "approved":
                return self.project_view(principal, project_id)
            row.status = "approved"
            row.approved_by = principal["id"]
            row.approved_at = utcnow()
            self._event(db, principal, project_id, "contract_approved", "Approved a result contract. The repair worker cannot edit it.")
            db.commit()
        return self.project_view(principal, project_id)

    def approve_proposal(self, principal: dict, project_id: str, proposal_id: str, contract_id: str) -> dict:
        self._require_project(principal, project_id, writable=True)
        with self.store.session() as db:
            proposal = self._proposal(db, principal["tenant_id"], proposal_id)
            contract = self._contract(db, principal["tenant_id"], contract_id)
            snapshot = self._snapshot(db, principal["tenant_id"], proposal.snapshot_id)
            if proposal.project_id != project_id or contract.project_id != project_id or snapshot.project_id != project_id:
                raise RetraceError("not_found", "That approval does not belong to this project.", "Choose a contract and a repair from the same project.", status=404)
            if contract.status != "approved":
                raise RetraceError(
                    "contract_not_approved",
                    "Approve the result contract before approving a repair.",
                    "Open the contract and approve it. The expected values stay visible.",
                )
            files = self._files(db, snapshot.id)
            candidate = apply_notebook_edit(files[proposal.file], proposal.find_text, proposal.replace_text)
            candidate_hash = sha256_bytes(candidate)
            self.store.put_bytes(candidate)
            action = sha256_json(
                {
                    "actor": principal["id"],
                    "candidate": candidate_hash,
                    "contract": contract.body_hash,
                    "patch": proposal.patch_hash,
                    "snapshot": snapshot.content_hash,
                }
            )
            approval = Approval(
                id=self.store.new_id(),
                tenant_id=principal["tenant_id"],
                proposal_id=proposal.id,
                contract_id=contract.id,
                contract_hash=contract.body_hash,
                snapshot_hash=snapshot.content_hash,
                patch_hash=proposal.patch_hash,
                candidate_hash=candidate_hash,
                actor_id=principal["id"],
                action_digest=action,
                created_at=utcnow(),
            )
            proposal.status = "approved"
            db.add(approval)
            self._event(db, principal, project_id, "repair_approved", f"Approved “{proposal.title}” against contract {contract.body_hash[:12]}.")
            db.commit()
            approval_id = approval.id
        return {"approval_id": approval_id, "project": self.project_view(principal, project_id)}

    def run_baseline(self, principal: dict, project_id: str, idempotency_key: str) -> dict:
        return self._run(principal, project_id, idempotency_key, approval_id=None)

    def run_approval(self, principal: dict, project_id: str, approval_id: str, idempotency_key: str) -> dict:
        return self._run(principal, project_id, idempotency_key, approval_id=approval_id)

    def cancel_run(self, principal: dict, project_id: str, run_id: str) -> dict:
        with self.store.session() as db:
            run = db.get(Run, run_id)
            if run is None or run.tenant_id != principal["tenant_id"] or run.project_id != project_id:
                raise RetraceError("not_found", "That run is not in this project.", "Refresh the project and choose a run that is listed.", status=404)
            if run.finished_at is not None:
                raise RetraceError(
                    "already_finished",
                    "This run has already finished. Cancelling it cannot change the recorded outcome.",
                    "Start a new run if you want a different comparison.",
                    status=409,
                )
            run.execution_status = "CANCELLED"
            run.verification_status = "NOT_RUN"
            run.explanation = "Cancelled before execution."
            run.finished_at = utcnow()
            db.commit()
        return self.project_view(principal, project_id)

    def export_bundle(self, principal: dict, project_id: str, run_id: str) -> bytes:
        view = self.project_view(principal, project_id)
        run = next((item for item in view["runs"] if item["id"] == run_id), None)
        if run is None:
            raise RetraceError("not_found", "That run is not in this project.", "Choose a finished run from the list.", status=404)
        with self.store.session() as db:
            snapshot = self._snapshot_for_project(db, principal["tenant_id"], project_id)
            files = self._files(db, snapshot.id)
            contract = next(item for item in view["contracts"] if item["id"] == run["contract_id"]) if run["contract_id"] else None
            proposal = next((item for item in view["proposals"] if item["id"] == run["proposal_id"]), None)
        packed: dict[str, bytes] = {f"snapshot/{path}": data for path, data in files.items()}
        limitations = (
            "Agreement with a result contract is a computational comparison, not proof of a scientific conclusion. "
            "A notebook can still be written to emit internally consistent numbers. "
            "This bundle is a Workflow Run RO-Crate subset and has not passed a full profile validator. "
            "The claimed verification status inside the bundle is not authoritative on another machine until that machine reruns the comparison. "
            "Demonstration faults are injected.\n"
        )
        if proposal is not None:
            packed["patch.json"] = json.dumps(
                {
                    "file": proposal["file"],
                    "find": proposal["find_text"],
                    "replace": proposal["replace_text"],
                    "classification": proposal["classification"],
                    "injected": proposal["injected"],
                    "author": proposal["author"],
                    "rationale": proposal["rationale"],
                    "title": proposal["title"],
                },
                indent=2,
            ).encode()
            candidate = apply_notebook_edit(files[proposal["file"]], proposal["find_text"], proposal["replace_text"])
            packed[f"candidate/{proposal['file']}"] = candidate
        if contract is not None:
            packed["contract.json"] = json.dumps(contract["body"], indent=2, sort_keys=True).encode()
        packed["verification.json"] = json.dumps(
            {
                "claimed_execution_status": run["execution_status"],
                "claimed_verification_status": run["verification_status"],
                "explanation": run["explanation"],
                "checks": run["checks"],
                "authoritative_on_import": False,
            },
            indent=2,
        ).encode()
        packed["limitations.txt"] = limitations.encode()
        document = {
            "title": view["project"]["name"],
            "created_at": run["finished_at"] or run["started_at"],
            "limitations": limitations.strip(),
            "claimed_verification_status": run["verification_status"],
            "authoritative_on_import": False,
            "snapshot_hash": view["snapshot"]["content_hash"],
            "notebook_path": view["snapshot"]["notebook_path"],
            "discipline": view["project"]["discipline"],
            "question": view["project"]["question"],
            "demo_slug": view["project"]["demo_slug"],
        }
        return build_bundle(document, packed)

    def import_bundle(self, principal: dict, payload: bytes) -> dict:
        document, files = read_bundle(payload)
        snapshot_files = {}
        for path, data in files.items():
            if path.startswith("snapshot/"):
                snapshot_files[path.removeprefix("snapshot/")] = data
        if not snapshot_files:
            raise RetraceError("bad_bundle", "The bundle has no snapshot files.", "Export the bundle again from a finished run.")
        self._reject_unsafe_tree(snapshot_files)
        notebooks = [path for path in snapshot_files if path.endswith(".ipynb")]
        if len(notebooks) != 1:
            raise RetraceError("bad_bundle", "The snapshot inside the bundle does not contain one notebook.", "Export the bundle again.")
        contract_bytes = files.get("contract.json")
        patch_bytes = files.get("patch.json")
        now = utcnow()
        with self.store.session() as db:
            project = Project(
                id=self.store.new_id(),
                tenant_id=principal["tenant_id"],
                name=f"Imported · {document.get('title', 'Evidence')}"[:160],
                discipline=str(document.get("discipline") or ""),
                question=str(document.get("question") or ""),
                demo_slug=document.get("demo_slug"),
                version=1,
                created_at=now,
            )
            db.add(project)
            self._insert_snapshot(db, principal["tenant_id"], project.id, snapshot_files, notebooks[0], now)
            if contract_bytes:
                body = json.loads(contract_bytes.decode())
                ResultContract.model_validate(body)
                self._insert_contract(db, principal, project.id, body, 1)
            if patch_bytes and contract_bytes:
                patch = json.loads(patch_bytes.decode())
                snapshot = self._snapshot_for_project(db, principal["tenant_id"], project.id)
                self._insert_proposal(
                    db,
                    principal,
                    project.id,
                    snapshot,
                    snapshot_files,
                    slug="imported-patch",
                    title=str(patch.get("title") or "Imported repair"),
                    claimed=str(patch.get("classification") or "methodological_reanalysis"),
                    author=str(patch.get("author") or "imported-bundle"),
                    injected=bool(patch.get("injected")),
                    rationale=str(patch.get("rationale") or "Imported from an evidence bundle. The claimed status was not trusted."),
                    find=str(patch["find"]),
                    replace=str(patch["replace"]),
                )
            claimed = document.get("claimed_verification_status")
            self._event(
                db,
                principal,
                project.id,
                "bundle_imported",
                f"Imported an evidence bundle. Claimed status was {claimed}. It is not a verification on this machine.",
            )
            db.commit()
            project_id = project.id
        return self.project_view(principal, project_id)

    def save_layout(self, principal: dict, project_id: str, body: dict, expected_version: int) -> dict:
        self._require_project(principal, project_id)
        from retrace.uiplan import validate_plan

        plan = validate_plan(body)
        with self.store.session() as db:
            row = db.scalar(
                select(Layout).where(
                    Layout.tenant_id == principal["tenant_id"],
                    Layout.principal_id == principal["id"],
                    Layout.project_id == project_id,
                )
            )
            if row is None:
                if expected_version not in {0, 1}:
                    raise RetraceError("version_conflict", "The layout was saved from another view.", "Reload the workspace and apply the layout again.", status=409)
                row = Layout(
                    id=self.store.new_id(),
                    tenant_id=principal["tenant_id"],
                    principal_id=principal["id"],
                    project_id=project_id,
                    version=1,
                    body_json=json.dumps(plan),
                )
                db.add(row)
            else:
                if row.version != expected_version:
                    raise RetraceError("version_conflict", "The layout changed since you loaded it.", "Reload the workspace. Your undo stack still has the previous arrangement.", status=409)
                row.version += 1
                row.body_json = json.dumps(plan)
            db.commit()
            version = row.version
        return {"version": version, "plan": plan}

    def rename_project(self, principal: dict, project_id: str, name: str, expected_version: int) -> dict:
        cleaned = " ".join(name.split())
        if not cleaned or len(cleaned) > 160:
            raise RetraceError("bad_name", "Give the project a name of up to 160 characters.", "Edit the name and save again.")
        with self.store.session() as db:
            project = self._project_row(db, principal["tenant_id"], project_id)
            if project.retired_at is not None:
                raise RetraceError("retired", "This project is retired and cannot be renamed.", "Import the evidence bundle into a new project if you need a working copy.", status=409)
            if project.version != expected_version:
                raise RetraceError("version_conflict", "The project was updated somewhere else.", "Reload the project before renaming it.", status=409)
            project.name = cleaned
            project.version += 1
            self._event(db, principal, project_id, "renamed", f"Renamed the project to {cleaned}.")
            db.commit()
        return self.project_view(principal, project_id)

    def retire_project(self, principal: dict, project_id: str, confirmation: str) -> dict:
        if confirmation != "RETIRE":
            raise RetraceError(
                "confirmation_required",
                "Retiring a project hides it from the desk. Type RETIRE to confirm.",
                "The snapshot and runs stay stored. This does not rewrite them.",
            )
        with self.store.session() as db:
            project = self._project_row(db, principal["tenant_id"], project_id)
            project.retired_at = utcnow()
            self._event(db, principal, project_id, "retired", "Retired the project. Records were not rewritten.")
            db.commit()
        return {"retired": True, "project_id": project_id}

    def draft_wiki(self, principal: dict, project_id: str) -> dict:
        view = self.project_view(principal, project_id)
        if not view["contracts"]:
            body = (
                f"# {view['project']['name']}\n\n"
                "No result contract is on this project. There is nothing to claim.\n\n"
                f"Snapshot anchor: #snapshot-{view['snapshot']['id']}\n"
            )
            status = "abstained"
        else:
            lines = [
                f"# {view['project']['name']}",
                "",
                "Draft assembled from project records. It is not a literature claim and it is not primary evidence.",
                "",
                f"Question: {view['project']['question'] or 'Not stated.'}",
                "",
                f"Snapshot: #snapshot-{view['snapshot']['id']} `{view['snapshot']['content_hash']}`",
            ]
            for contract in view["contracts"]:
                lines.append(f"Contract: #contract-{contract['id']} status {contract['status']} `{contract['body_hash']}`")
            for run in view["runs"]:
                lines.append(
                    f"Run: #run-{run['id']} execution {run['execution_status']} verification {run['verification_status']}"
                )
            lines.append("")
            lines.append("Generated text on this page does not replace the result contract or the verifier output.")
            body = "\n".join(lines) + "\n"
            status = "draft"
        with self.store.session() as db:
            row = db.scalar(select(WikiPage).where(WikiPage.project_id == project_id, WikiPage.tenant_id == principal["tenant_id"]))
            if row is None:
                row = WikiPage(
                    id=self.store.new_id(),
                    tenant_id=principal["tenant_id"],
                    project_id=project_id,
                    status=status,
                    body=body,
                    version=1,
                )
                db.add(row)
            else:
                row.body = body
                row.status = status
                row.version += 1
            db.commit()
            return {"id": row.id, "status": row.status, "body": row.body, "version": row.version, "review": "NOT_REVIEWED"}

    def review_wiki(self, principal: dict, project_id: str) -> dict:
        with self.store.session() as db:
            row = db.scalar(select(WikiPage).where(WikiPage.project_id == project_id, WikiPage.tenant_id == principal["tenant_id"]))
            if row is None:
                raise RetraceError("not_found", "Draft a wiki page before marking it reviewed.", "Open the project wiki and create the draft.", status=404)
            if row.status == "abstained":
                raise RetraceError(
                    "nothing_to_review",
                    "This page abstained because the project has no contract. There is no claim to accept.",
                    "Add a result contract before review.",
                )
            row.status = "reviewed"
            row.version += 1
            self._event(db, principal, project_id, "wiki_reviewed", "A person marked the record draft reviewed. The draft is still not primary evidence.")
            db.commit()
            return {"id": row.id, "status": row.status, "body": row.body, "version": row.version, "review": "REVIEWED_BY_OPERATOR"}

    def add_event_time(self, principal: dict, title: str, local_start: str, zone: str, fold: int | None) -> dict:
        try:
            tz = ZoneInfo(zone)
        except ZoneInfoNotFoundError as exc:
            raise RetraceError("bad_zone", "That time zone is not a recognised IANA name.", "Use an IANA zone such as Europe/London.") from exc
        try:
            naive = datetime_from_local(local_start)
        except ValueError as exc:
            raise RetraceError("bad_time", "The local time could not be read.", "Use a time like 2026-11-01T01:30.") from exc
        first = naive.replace(tzinfo=tz, fold=0).astimezone(timezone.utc)
        second = naive.replace(tzinfo=tz, fold=1).astimezone(timezone.utc)
        if first != second and fold not in {0, 1}:
            raise RetraceError(
                "ambiguous_local_time",
                f"That local time happens twice in {zone}: {iso(first)} and {iso(second)}.",
                "Submit fold 0 for the earlier instant or fold 1 for the later instant.",
                status=409,
            )
        chosen = second if fold == 1 and first != second else first
        with self.store.session() as db:
            row = CalendarEvent(
                id=self.store.new_id(),
                tenant_id=principal["tenant_id"],
                title=title[:160],
                start_utc=iso(chosen) or "",
                zone=zone,
                version=1,
            )
            db.add(row)
            db.commit()
            return {"id": row.id, "title": row.title, "start_utc": row.start_utc, "zone": row.zone, "version": row.version}

    def calendar(self, principal: dict) -> list[dict]:
        with self.store.session() as db:
            rows = db.scalars(select(CalendarEvent).where(CalendarEvent.tenant_id == principal["tenant_id"])).all()
            return [{"id": row.id, "title": row.title, "start_utc": row.start_utc, "zone": row.zone, "version": row.version} for row in rows]

    def calendar_ics(self, principal: dict) -> str:
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//RETRACE//Workstation//EN"]
        for event in self.calendar(principal):
            stamp = event["start_utc"].replace("-", "").replace(":", "")
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{event['id']}@retrace.local",
                    f"DTSTAMP:{stamp}",
                    f"DTSTART:{stamp}",
                    f"SUMMARY:{event['title']}",
                    f"DESCRIPTION:Stored in UTC. Organised in {event['zone']}.",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    def project_view(self, principal: dict, project_id: str) -> dict:
        with self.store.session() as db:
            project = self._project_row(db, principal["tenant_id"], project_id)
            snapshot = self._snapshot_for_project(db, principal["tenant_id"], project_id)
            file_rows = db.scalars(select(SnapshotFile).where(SnapshotFile.snapshot_id == snapshot.id, SnapshotFile.tenant_id == principal["tenant_id"])).all()
            notebook = ""
            file_info = []
            for row in file_rows:
                file_info.append({"path": row.path, "sha256": row.sha256, "size": row.size})
                if row.path == snapshot.notebook_path:
                    notebook = self.store.read_bytes(row.sha256).decode("utf-8")
            contracts = db.scalars(select(ContractRow).where(ContractRow.project_id == project_id, ContractRow.tenant_id == principal["tenant_id"]).order_by(ContractRow.version)).all()
            proposals = db.scalars(select(Proposal).where(Proposal.project_id == project_id, Proposal.tenant_id == principal["tenant_id"])).all()
            approvals = db.scalars(select(Approval).where(Approval.tenant_id == principal["tenant_id"])).all()
            approvals = [row for row in approvals if row.proposal_id in {item.id for item in proposals}]
            approval_contract = {row.id: row.contract_id for row in approvals}
            runs = db.scalars(select(Run).where(Run.project_id == project_id, Run.tenant_id == principal["tenant_id"]).order_by(Run.started_at)).all()
            events = db.scalars(select(Event).where(Event.project_id == project_id, Event.tenant_id == principal["tenant_id"]).order_by(Event.id)).all()
            layout = db.scalar(
                select(Layout).where(
                    Layout.project_id == project_id,
                    Layout.principal_id == principal["id"],
                    Layout.tenant_id == principal["tenant_id"],
                )
            )
            wiki = db.scalar(select(WikiPage).where(WikiPage.project_id == project_id, WikiPage.tenant_id == principal["tenant_id"]))
            allowlisted = snapshot.content_hash in allowlist()
            return {
                "project": self._project_brief(project),
                "snapshot": {
                    "id": snapshot.id,
                    "content_hash": snapshot.content_hash,
                    "notebook_path": snapshot.notebook_path,
                    "notebook_json": notebook,
                    "allowlisted": allowlisted,
                    "execution": "admitted-demonstration" if allowlisted else "inspection-only",
                    "files": file_info,
                },
                "contracts": [self._contract_out(row) for row in contracts],
                "proposals": [self._proposal_out(row) for row in proposals],
                "approvals": [self._approval_out(row) for row in approvals],
                "runs": [self._run_out(row, approval_contract) for row in runs],
                "events": [{"at": iso(row.at), "kind": row.kind, "summary": row.summary, "actor_id": row.actor_id} for row in events],
                "lineage": self._lineage(snapshot, file_info, contracts, proposals, approvals, runs),
                "layout": None if layout is None else {"version": layout.version, "plan": json.loads(layout.body_json)},
                "wiki": None if wiki is None else {"id": wiki.id, "status": wiki.status, "body": wiki.body, "version": wiki.version},
            }

    def _run(self, principal: dict, project_id: str, idempotency_key: str, approval_id: str | None) -> dict:
        if not idempotency_key or len(idempotency_key) > 120:
            raise RetraceError("bad_idempotency_key", "Give this run an idempotency key.", "Reuse the same key if you need to retry without starting a second run.")
        self._require_project(principal, project_id, writable=True)
        with self.store.session() as db:
            existing = db.scalar(
                select(Run).where(Run.tenant_id == principal["tenant_id"], Run.idempotency_key == idempotency_key)
            )
            if existing is not None:
                existing_id = existing.id
                project_for_existing = existing.project_id
            else:
                existing_id = None
                project_for_existing = None
        if existing_id is not None:
            return {"run_id": existing_id, "replayed": True, "project": self.project_view(principal, project_for_existing)}

        with self.store.session() as db:
            snapshot = self._snapshot_for_project(db, principal["tenant_id"], project_id)
            files = self._files(db, snapshot.id)
            notebook_path = snapshot.notebook_path
            classification = "execution_repair"
            contract_body = None
            contract_id = None
            proposal_id = None
            candidate_hash = None
            if approval_id is None:
                candidate_files = dict(files)
                label = "baseline"
            else:
                approval = db.get(Approval, approval_id)
                if approval is None or approval.tenant_id != principal["tenant_id"]:
                    raise RetraceError("not_found", "That approval is not on this workstation account.", "Approve the repair again from the project.", status=404)
                if approval.invalidated_at is not None:
                    raise RetraceError("approval_invalid", approval.invalid_reason or "The approval is no longer valid.", "Review the repair and approve the current candidate.", status=409)
                proposal = self._proposal(db, principal["tenant_id"], approval.proposal_id)
                contract = self._contract(db, principal["tenant_id"], approval.contract_id)
                if proposal.project_id != project_id or snapshot.content_hash != approval.snapshot_hash:
                    self._invalidate(db, approval, "The snapshot or project no longer matches the approval.")
                    db.commit()
                    raise RetraceError("approval_invalid", "The snapshot changed after approval.", "Approve the repair against the current snapshot.", status=409)
                if contract.body_hash != approval.contract_hash or proposal.patch_hash != approval.patch_hash:
                    self._invalidate(db, approval, "The contract or the repair text changed after approval.")
                    db.commit()
                    raise RetraceError("approval_invalid", "The approved repair or contract changed.", "Approve the current repair again. The previous approval no longer applies.", status=409)
                candidate = apply_notebook_edit(files[proposal.file], proposal.find_text, proposal.replace_text)
                candidate_hash = sha256_bytes(candidate)
                if candidate_hash != approval.candidate_hash:
                    self._invalidate(db, approval, "The candidate notebook bytes changed after approval.")
                    db.commit()
                    raise RetraceError("approval_invalid", "The candidate notebook no longer matches the approval.", "Approve the repair again.", status=409)
                candidate_files = dict(files)
                candidate_files[proposal.file] = candidate
                classification = proposal.classification
                contract_body = json.loads(contract.body_json)
                contract_id = contract.id
                proposal_id = proposal.id
                label = proposal.title
            allowlisted = snapshot.content_hash in allowlist()
            run = Run(
                id=self.store.new_id(),
                tenant_id=principal["tenant_id"],
                project_id=project_id,
                approval_id=approval_id,
                proposal_id=proposal_id,
                idempotency_key=idempotency_key,
                execution_status="QUEUED",
                verification_status="NOT_RUN",
                explanation="",
                checks_json="[]",
                log_text="",
                candidate_hash=candidate_hash,
                started_at=utcnow(),
            )
            db.add(run)
            db.commit()
            run_id = run.id
            contract_for_verify = contract_body
            files_for_run = candidate_files
            notebook_for_run = notebook_path
            class_for_verify = classification
            title = label
            is_allowed = allowlisted

        if not is_allowed:
            execution_status = "BLOCKED_UNSANDBOXED"
            results = None
            malformed = False
            log = "Refused. This workstation profile does not execute packages outside the admitted demonstrations, because no tested sandbox is configured."
        else:
            try:
                execution = execute_workspace(files_for_run, notebook_for_run)
            except Exception as exc:  # noqa: BLE001 — record the failure; do not invent a result
                execution_status = "FAILED"
                results = None
                malformed = False
                log = f"{type(exc).__name__}: {exc}"[:4000]
            else:
                execution_status = execution.status
                results = execution.results
                malformed = execution.malformed_output
                log = execution.log

        if contract_for_verify is None:
            if execution_status == "FAILED":
                verification, explanation, checks = (
                    "FAILED_EXECUTION",
                    "The untouched notebook failed. No repair has been applied and no reproduction is claimed.",
                    [],
                )
            elif execution_status == "BLOCKED_UNSANDBOXED":
                verification, explanation, checks = (
                    "NOT_RUN",
                    log,
                    [],
                )
            else:
                verification, explanation, checks = (
                    "EXECUTED_NOT_VERIFIED",
                    "The notebook finished and no result contract was selected, so nothing was verified.",
                    [],
                )
        else:
            public_results = None if results is None else {key: value for key, value in results.items() if key != "verification_status"}
            verification, explanation, checks = verify(
                contract=contract_for_verify,
                results=public_results,
                execution_status=execution_status,
                classification=class_for_verify,
                malformed_output=malformed,
            )
        with self.store.session() as db:
            run = db.get(Run, run_id)
            assert run is not None
            run.execution_status = execution_status
            run.verification_status = verification
            run.explanation = explanation
            run.results_json = None if results is None else json.dumps(results)
            run.checks_json = json.dumps(checks)
            run.log_text = log
            run.finished_at = utcnow()
            self._event(db, principal, project_id, "run_finished", f"{title}: execution {execution_status}, verification {verification}.")
            db.commit()
        return {"run_id": run_id, "replayed": False, "project": self.project_view(principal, project_id)}

    def _insert_snapshot(self, db, tenant_id: str, project_id: str, files: dict[str, bytes], notebook_path: str, now) -> Snapshot:
        snapshot = Snapshot(
            id=self.store.new_id(),
            tenant_id=tenant_id,
            project_id=project_id,
            content_hash=snapshot_content_hash(files),
            notebook_path=notebook_path,
            created_at=now,
        )
        db.add(snapshot)
        for path, data in files.items():
            digest = self.store.put_bytes(data)
            db.add(
                SnapshotFile(
                    snapshot_id=snapshot.id,
                    tenant_id=tenant_id,
                    path=path,
                    sha256=digest,
                    size=len(data),
                )
            )
        return snapshot

    def _insert_contract(self, db, principal: dict, project_id: str, body: dict, version: int) -> ContractRow:
        validated = ResultContract.model_validate(body)
        encoded = validated.model_dump()
        row = ContractRow(
            id=self.store.new_id(),
            tenant_id=principal["tenant_id"],
            project_id=project_id,
            version=version,
            body_json=json.dumps(encoded, sort_keys=True),
            body_hash=sha256_json(encoded),
            status="draft",
        )
        db.add(row)
        return row

    def _insert_proposal(self, db, principal, project_id, snapshot, files, slug, title, claimed, author, injected, rationale, find, replace) -> None:
        original = files[snapshot.notebook_path]
        edited = apply_notebook_edit(original, find, replace)
        actual = assert_label_allowed(joined_code(original), joined_code(edited), claimed)
        proposal = Proposal(
            id=self.store.new_id(),
            tenant_id=principal["tenant_id"],
            project_id=project_id,
            snapshot_id=snapshot.id,
            slug=slug,
            title=title,
            classification=actual,
            author=author,
            injected=1 if injected else 0,
            rationale=rationale,
            file=snapshot.notebook_path,
            find_text=find,
            replace_text=replace,
            patch_hash=sha256_json({"file": snapshot.notebook_path, "find": find, "replace": replace}),
            status="proposed",
        )
        db.add(proposal)

    def _reject_unsafe_tree(self, files: dict[str, bytes]) -> None:
        if not files or len(files) > 20:
            raise RetraceError("bad_package", "Import between 1 and 20 files.", "Keep the package to the notebook and its tables.")
        for path, data in files.items():
            parts = Path(path).parts
            suffix = Path(path).suffix.lower()
            if not path or path.startswith("/") or "\\" in path or ".." in parts or any(part.startswith(".") for part in parts):
                raise RetraceError("bad_package", f"The path {path} is not allowed.", "Use relative names such as analysis.ipynb and data/table.csv.")
            if suffix in {".pkl", ".pickle"} or path.endswith(".pyc"):
                raise RetraceError("refused_file", "Pickle files are not admitted.", "Export tables as CSV and notebooks as .ipynb.")
            if suffix not in _ALLOWED_UPLOAD:
                raise RetraceError(
                    "unsupported_file",
                    f"{path} is outside the workstation format profile.",
                    "This profile admits .ipynb, .csv, .tsv, .txt, .md, and .json. Other formats are not pretended to convert.",
                )
            if len(data) > 2_000_000:
                raise RetraceError("file_too_large", f"{path} is larger than 2 MB.", "Use a smaller demonstration file.")
            if suffix == ".ipynb":
                try:
                    nbformat.reads(data.decode("utf-8"), as_version=4)
                except Exception as exc:  # noqa: BLE001
                    raise RetraceError("bad_notebook", f"{path} is not a readable notebook.", "Export the notebook as nbformat JSON.") from exc
            elif b"\0" in data:
                raise RetraceError("bad_file", f"{path} is not plain text.", "Upload a text table or notebook.")

    def _require_project(self, principal: dict, project_id: str, writable: bool = False) -> dict:
        with self.store.session() as db:
            project = self._project_row(db, principal["tenant_id"], project_id)
            if writable and project.retired_at is not None:
                raise RetraceError("retired", "This project is retired.", "Import a bundle into a new project to continue.", status=409)
            return self._project_brief(project)

    def _project_row(self, db, tenant_id: str, project_id: str) -> Project:
        project = db.get(Project, project_id)
        if project is None or project.tenant_id != tenant_id:
            raise RetraceError("not_found", "That project is not on this account.", "Open a project from your desk.", status=404)
        return project

    def _snapshot(self, db, tenant_id: str, snapshot_id: str) -> Snapshot:
        row = db.get(Snapshot, snapshot_id)
        if row is None or row.tenant_id != tenant_id:
            raise RetraceError("not_found", "That snapshot is not on this account.", "Import the package again.", status=404)
        return row

    def _snapshot_for_project(self, db, tenant_id: str, project_id: str) -> Snapshot:
        row = db.scalar(select(Snapshot).where(Snapshot.project_id == project_id, Snapshot.tenant_id == tenant_id))
        if row is None:
            raise RetraceError("not_found", "This project has no snapshot.", "Import a notebook package.", status=404)
        return row

    def _contract(self, db, tenant_id: str, contract_id: str) -> ContractRow:
        row = db.get(ContractRow, contract_id)
        if row is None or row.tenant_id != tenant_id:
            raise RetraceError("not_found", "That contract is not on this account.", "Choose a contract from the project.", status=404)
        return row

    def _proposal(self, db, tenant_id: str, proposal_id: str) -> Proposal:
        row = db.get(Proposal, proposal_id)
        if row is None or row.tenant_id != tenant_id:
            raise RetraceError("not_found", "That repair is not on this account.", "Choose a repair from the project.", status=404)
        return row

    def _files(self, db, snapshot_id: str) -> dict[str, bytes]:
        rows = db.scalars(select(SnapshotFile).where(SnapshotFile.snapshot_id == snapshot_id)).all()
        return {row.path: self.store.read_bytes(row.sha256) for row in rows}

    def _event(self, db, principal: dict, project_id: str | None, kind: str, summary: str) -> None:
        db.add(
            Event(
                tenant_id=principal["tenant_id"],
                project_id=project_id,
                at=utcnow(),
                actor_id=principal["id"],
                kind=kind,
                summary=summary,
            )
        )

    def _invalidate(self, db, approval: Approval, reason: str) -> None:
        approval.invalidated_at = utcnow()
        approval.invalid_reason = reason

    def _project_brief(self, project: Project) -> dict:
        return {
            "id": project.id,
            "name": project.name,
            "discipline": project.discipline,
            "question": project.question,
            "demo_slug": project.demo_slug,
            "version": project.version,
            "retired_at": iso(project.retired_at),
            "created_at": iso(project.created_at),
            "demo": project.demo_slug is not None,
        }

    def _contract_out(self, row: ContractRow) -> dict:
        return {
            "id": row.id,
            "version": row.version,
            "status": row.status,
            "body_hash": row.body_hash,
            "body": json.loads(row.body_json),
            "approved_by": row.approved_by,
            "approved_at": iso(row.approved_at),
        }

    def _proposal_out(self, row: Proposal) -> dict:
        return {
            "id": row.id,
            "slug": row.slug,
            "title": row.title,
            "classification": row.classification,
            "author": row.author,
            "injected": bool(row.injected),
            "rationale": row.rationale,
            "file": row.file,
            "find_text": row.find_text,
            "replace_text": row.replace_text,
            "patch_hash": row.patch_hash,
            "status": row.status,
        }

    def _approval_out(self, row: Approval) -> dict:
        return {
            "id": row.id,
            "proposal_id": row.proposal_id,
            "contract_id": row.contract_id,
            "contract_hash": row.contract_hash,
            "snapshot_hash": row.snapshot_hash,
            "patch_hash": row.patch_hash,
            "candidate_hash": row.candidate_hash,
            "action_digest": row.action_digest,
            "actor_id": row.actor_id,
            "created_at": iso(row.created_at),
            "invalidated_at": iso(row.invalidated_at),
            "invalid_reason": row.invalid_reason,
        }

    def _run_out(self, row: Run, approval_contract: dict[str, str]) -> dict:
        return {
            "id": row.id,
            "approval_id": row.approval_id,
            "proposal_id": row.proposal_id,
            "contract_id": None if row.approval_id is None else approval_contract.get(row.approval_id),
            "idempotency_key": row.idempotency_key,
            "execution_status": row.execution_status,
            "verification_status": row.verification_status,
            "explanation": row.explanation,
            "results": None if row.results_json is None else json.loads(row.results_json),
            "checks": json.loads(row.checks_json or "[]"),
            "log": row.log_text,
            "candidate_hash": row.candidate_hash,
            "started_at": iso(row.started_at),
            "finished_at": iso(row.finished_at),
        }

    def _lineage(self, snapshot, file_info, contracts, proposals, approvals, runs) -> dict:
        nodes = [
            {"id": snapshot.id, "type": "snapshot", "label": "Untouched snapshot", "status": "admitted"},
        ]
        edges = []
        for item in file_info:
            node_id = f"file:{item['path']}"
            nodes.append({"id": node_id, "type": "file", "label": item["path"], "status": "admitted"})
            edges.append({"source": node_id, "target": snapshot.id, "kind": "USED_BY", "observed": True})
        for contract in contracts:
            nodes.append({"id": contract.id, "type": "contract", "label": json.loads(contract.body_json)["title"], "status": contract.status})
        approved = {row.proposal_id for row in approvals if row.invalidated_at is None}
        for proposal in proposals:
            nodes.append(
                {
                    "id": proposal.id,
                    "type": "proposal",
                    "label": proposal.title,
                    "status": proposal.classification,
                }
            )
            edges.append(
                {
                    "source": proposal.id,
                    "target": snapshot.id,
                    "kind": "REPAIRS",
                    "observed": proposal.id in approved,
                }
            )
        for run in runs:
            nodes.append({"id": run.id, "type": "run", "label": run.verification_status, "status": run.execution_status})
            edges.append({"source": snapshot.id, "target": run.id, "kind": "PRODUCED", "observed": True})
            if run.approval_id:
                approval = next((item for item in approvals if item.id == run.approval_id), None)
                if approval is not None:
                    edges.append({"source": run.id, "target": approval.contract_id, "kind": "CHECKED_AGAINST", "observed": True})
                    edges.append({"source": approval.actor_id, "target": approval.id, "kind": "APPROVED_BY", "observed": True})
                    nodes.append({"id": approval.id, "type": "approval", "label": "Approval", "status": "invalid" if approval.invalidated_at else "bound"})
                    nodes.append({"id": approval.actor_id, "type": "person", "label": "Reviewer", "status": "observed"})
        return {"nodes": _unique_nodes(nodes), "edges": edges}


def _unique_nodes(nodes: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for node in nodes:
        if node["id"] in seen:
            continue
        seen.add(node["id"])
        unique.append(node)
    return unique


def datetime_from_local(value: str):
    from datetime import datetime

    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        raise ValueError("local time must not include an offset")
    return parsed
