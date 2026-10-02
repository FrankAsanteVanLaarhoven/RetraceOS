from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool

from retrace.hashing import sha256_bytes


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return as_utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Principal(Base):
    __tablename__ = "principals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(80), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionRow(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    principal_id: Mapped[str] = mapped_column(ForeignKey("principals.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    discipline: Mapped[str] = mapped_column(String(80), default="")
    question: Mapped[str] = mapped_column(Text, default="")
    demo_slug: Mapped[str | None] = mapped_column(String(40), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Snapshot(Base):
    __tablename__ = "snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    notebook_path: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SnapshotFile(Base):
    __tablename__ = "snapshot_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String(36), index=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    path: Mapped[str] = mapped_column(String(200))
    sha256: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)


class ContractRow(Base):
    __tablename__ = "contracts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    body_json: Mapped[str] = mapped_column(Text)
    body_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20))
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Proposal(Base):
    __tablename__ = "proposals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    snapshot_id: Mapped[str] = mapped_column(String(36))
    slug: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    classification: Mapped[str] = mapped_column(String(40))
    author: Mapped[str] = mapped_column(String(80))
    injected: Mapped[int] = mapped_column(Integer, default=0)
    rationale: Mapped[str] = mapped_column(Text)
    file: Mapped[str] = mapped_column(String(200))
    find_text: Mapped[str] = mapped_column(Text)
    replace_text: Mapped[str] = mapped_column(Text)
    patch_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20))


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    proposal_id: Mapped[str] = mapped_column(String(36))
    contract_id: Mapped[str] = mapped_column(String(36))
    contract_hash: Mapped[str] = mapped_column(String(64))
    snapshot_hash: Mapped[str] = mapped_column(String(64))
    patch_hash: Mapped[str] = mapped_column(String(64))
    candidate_hash: Mapped[str] = mapped_column(String(64))
    actor_id: Mapped[str] = mapped_column(String(36))
    action_digest: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invalid_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    approval_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    proposal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(120))
    execution_status: Mapped[str] = mapped_column(String(40))
    verification_status: Mapped[str] = mapped_column(String(40))
    explanation: Mapped[str] = mapped_column(Text)
    results_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    checks_json: Mapped[str] = mapped_column(Text, default="[]")
    log_text: Mapped[str] = mapped_column(Text, default="")
    candidate_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_id: Mapped[str] = mapped_column(String(36))
    kind: Mapped[str] = mapped_column(String(40))
    summary: Mapped[str] = mapped_column(Text)


class Layout(Base):
    __tablename__ = "layouts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    principal_id: Mapped[str] = mapped_column(String(36))
    project_id: Mapped[str] = mapped_column(String(36))
    version: Mapped[int] = mapped_column(Integer, default=1)
    body_json: Mapped[str] = mapped_column(Text)


class WikiPage(Base):
    __tablename__ = "wiki_pages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    project_id: Mapped[str] = mapped_column(String(36), unique=True)
    status: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(160))
    start_utc: Mapped[str] = mapped_column(String(40))
    zone: Mapped[str] = mapped_column(String(80))
    version: Mapped[int] = mapped_column(Integer, default=1)


class Preference(Base):
    __tablename__ = "preferences"
    principal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    theme: Mapped[str] = mapped_column(String(20), default="system")
    density: Mapped[str] = mapped_column(String(20), default="comfortable")
    zone: Mapped[str] = mapped_column(String(80), default="UTC")
    locale: Mapped[str] = mapped_column(String(20), default="en")


class ObjectBlob(Base):
    """Notebook bytes kept in the database when the host has no durable disk."""

    __tablename__ = "object_blobs"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    data: Mapped[bytes] = mapped_column(LargeBinary)


class ConnectorSecret(Base):
    """A token the person saved for their own account. API responses never include secret."""

    __tablename__ = "connector_secrets"
    principal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    connector_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    secret: Mapped[str] = mapped_column(Text)
    label: Mapped[str] = mapped_column(String(120), default="")


def sqlalchemy_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Store:
    def __init__(self, database: Path, objects: Path, database_url: str | None = None) -> None:
        objects.mkdir(parents=True, exist_ok=True)
        self.database = database
        self.objects = objects
        self.database_url = sqlalchemy_url(database_url) if database_url else f"sqlite:///{database}"
        self.objects_in_database = not self.database_url.startswith("sqlite")
        kwargs: dict = {"poolclass": NullPool} if self.objects_in_database else {"connect_args": {"check_same_thread": False}}
        self.engine = create_engine(self.database_url, **kwargs)
        Base.metadata.create_all(self.engine)
        if self.engine.dialect.name == "sqlite":
            self._ensure_preference_locale()
        self._sessions = sessionmaker(self.engine, expire_on_commit=False)

    def _ensure_preference_locale(self) -> None:
        """create_all does not add columns to a database that already exists."""
        with self.engine.begin() as connection:
            rows = connection.exec_driver_sql("PRAGMA table_info(preferences)").fetchall()
            names = {row[1] for row in rows}
            if rows and "locale" not in names:
                connection.exec_driver_sql("ALTER TABLE preferences ADD COLUMN locale VARCHAR(20) NOT NULL DEFAULT 'en'")

    def session(self) -> Session:
        return self._sessions()

    def put_bytes(self, data: bytes) -> str:
        digest = sha256_bytes(data)
        if self.objects_in_database:
            with self.session() as db:
                if db.get(ObjectBlob, digest) is None:
                    db.add(ObjectBlob(digest=digest, data=data))
                    db.commit()
            return digest
        path = self.objects / digest
        if not path.exists():
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(path)
        return digest

    def read_bytes(self, digest: str) -> bytes:
        if self.objects_in_database:
            with self.session() as db:
                row = db.get(ObjectBlob, digest)
                if row is None:
                    raise FileNotFoundError(digest)
                return bytes(row.data)
        return (self.objects / digest).read_bytes()

    def drop_unreferenced(self, digest: str) -> None:
        if self.objects_in_database:
            with self.session() as db:
                row = db.get(ObjectBlob, digest)
                if row is not None:
                    db.delete(row)
                    db.commit()
            return
        path = self.objects / digest
        if path.is_file():
            path.unlink()

    def new_id(self) -> str:
        return secrets.token_hex(16)

    def save_connector_secret(self, principal_id: str, connector_id: str, secret: str, label: str) -> None:
        with self.session() as db:
            row = db.get(ConnectorSecret, (principal_id, connector_id))
            if row is None:
                db.add(ConnectorSecret(principal_id=principal_id, connector_id=connector_id, secret=secret, label=label[:120]))
            else:
                row.secret = secret
                row.label = label[:120]
            db.commit()

    def connector_secret(self, principal_id: str, connector_id: str) -> tuple[str, str] | None:
        with self.session() as db:
            row = db.get(ConnectorSecret, (principal_id, connector_id))
            if row is None:
                return None
            return row.secret, row.label

    def clear_connector_secret(self, principal_id: str, connector_id: str) -> None:
        with self.session() as db:
            row = db.get(ConnectorSecret, (principal_id, connector_id))
            if row is not None:
                db.delete(row)
                db.commit()
