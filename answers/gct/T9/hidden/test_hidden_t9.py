"""Hidden tests for T9: replacing an uploaded file's contents with PUT /files/{file_id}.

They drive the real app (create_app, stub providers, the test's owner) and the real worker
(`process_one` on a connection holding the worker lock), with real PDFs. The rules checked are the
ones the ticket states before any of the work: a ready file keeps answering from its current
content until the new version is published, a failed replacement leaves the file as it was, nothing
staged is deleted, refusals stage nothing, and the filename changes only on publish.
"""

from __future__ import annotations

import io
import uuid
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.config import EMBEDDING_DIM, STAGING_DIR
from gct.ingest.chunk import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from gct.jobs import worker
from gct.jobs.worker import process_one
from gct.providers.base import TransientEmbeddingError
from gct.retriever.retrieve import retrieve

VEC = [1.0] + [0.0] * (EMBEDDING_DIM - 1)


class FakeEmbeddings:
    model_id = "fake-embed-3"
    dim = EMBEDDING_DIM

    def __init__(self, transient_failures: int = 0) -> None:
        self.calls = 0
        self._failures_left = transient_failures

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls += 1
        if self._failures_left > 0:
            self._failures_left -= 1
            raise TransientEmbeddingError("simulated provider 429")
        return [list(VEC) for _ in texts]


class StubGeneration:
    model_id = "stub-gen"

    def generate(self, messages) -> str:
        return ""


def pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(612, 792))
    c.drawString(72, 700, text)
    c.showPage()
    c.save()
    return buf.getvalue()


CORRUPT = b"%PDF-1.7\nthis is not a PDF at all\n"


@pytest.fixture
def app_and_client(worker_db):
    _, owner, _ = worker_db
    app = create_app(embedder=FakeEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as client:
        yield app, client


def tick(conn, embedder=None, **kw) -> bool:
    return process_one(
        conn,
        embedder=embedder or FakeEmbeddings(),
        chunk_size=CHUNK_SIZE_WORDS,
        chunk_overlap=CHUNK_OVERLAP_WORDS,
        **kw,
    )


def upload(client, class_id: str, name: str, content: bytes) -> str:
    r = client.post(
        "/files", data={"class_id": class_id}, files={"file": (name, content, "application/pdf")}
    )
    assert r.status_code == 202, r.text
    return r.json()["file_id"]


def replace(client, file_id: str, name: str, content: bytes):
    return client.put(f"/files/{file_id}", files={"file": (name, content, "application/pdf")})


def texts(conn, owner_id: str, class_id: str) -> set[str]:
    got = retrieve(conn, "anything", owner_id, class_id, embedder=FakeEmbeddings(), k=20)
    return {c.text for c in got}


def staging_refs(db_other, file_id: str) -> str:
    return db_other.execute(
        "select staging_ref from files where file_id = %s::uuid", (file_id,)
    ).fetchone()[0]


def staged_files() -> set[Path]:
    root = Path(STAGING_DIR)
    return {p for p in root.rglob("*") if p.is_file()} if root.exists() else set()


def test_a_ready_file_keeps_answering_until_the_new_version_is_published(
    app_and_client, worker_db, db_other
):
    _, client = app_and_client
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    file_id = upload(client, class_id, "week-1.pdf", pdf("the old lecture text"))
    assert tick(conn) is True
    old_ref = staging_refs(db_other, file_id)

    r = replace(client, file_id, "week-1-v2.pdf", pdf("the new lecture text"))
    assert r.status_code == 202, r.text
    assert r.json()["file_id"] == file_id
    assert r.json()["filename"] == "week-1-v2.pdf"

    body = client.get(f"/files/{file_id}").json()
    assert body["status"] == "ready"
    assert body["replacement"] == "pending"
    assert body["replacement_failed_reason"] is None
    assert body["filename"] == "week-1.pdf", "the name changes only on publish"
    assert texts(conn, owner_id, class_id) == {"the old lecture text"}

    assert tick(conn) is True
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["replacement"], body["filename"]) == (
        "ready",
        None,
        "week-1-v2.pdf",
    )
    assert texts(conn, owner_id, class_id) == {"the new lecture text"}
    new_ref = staging_refs(db_other, file_id)
    assert new_ref != old_ref and Path(new_ref).name == "week-1-v2.pdf"
    assert Path(old_ref).exists(), "nothing staged is deleted (ADR 0010)"


def test_a_failed_replacement_leaves_the_file_as_it_was(app_and_client, worker_db, db_other):
    _, client = app_and_client
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    file_id = upload(client, class_id, "notes.pdf", pdf("the good notes"))
    assert tick(conn) is True
    old_ref = staging_refs(db_other, file_id)

    assert replace(client, file_id, "notes-v2.pdf", CORRUPT).status_code == 202
    assert tick(conn) is True
    body = client.get(f"/files/{file_id}").json()
    assert body["status"] == "ready"
    assert body["failed_reason"] is None
    assert body["replacement"] == "failed"
    assert body["replacement_failed_reason"] == "unparseable"
    assert body["filename"] == "notes.pdf"
    assert texts(conn, owner_id, class_id) == {"the good notes"}
    assert staging_refs(db_other, file_id) == old_ref

    # A later replacement clears the failure and goes through.
    assert replace(client, file_id, "notes-v3.pdf", pdf("the better notes")).status_code == 202
    body = client.get(f"/files/{file_id}").json()
    assert (body["replacement"], body["replacement_failed_reason"]) == ("pending", None)
    assert tick(conn) is True
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["replacement"], body["replacement_failed_reason"]) == (
        "ready",
        None,
        None,
    )
    assert body["filename"] == "notes-v3.pdf"
    assert texts(conn, owner_id, class_id) == {"the better notes"}


def test_replacing_a_failed_file_processes_it_like_a_new_upload(app_and_client, worker_db):
    _, client = app_and_client
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    file_id = upload(client, class_id, "broken.pdf", CORRUPT)
    assert tick(conn) is True
    assert client.get(f"/files/{file_id}").json()["failed_reason"] == "unparseable"

    assert replace(client, file_id, "fixed.pdf", pdf("now it parses")).status_code == 202
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["failed_reason"], body["replacement"]) == ("queued", None, None)

    assert tick(conn) is True
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["filename"], body["replacement"]) == ("ready", "fixed.pdf", None)
    assert texts(conn, owner_id, class_id) == {"now it parses"}


def test_refusals_stage_nothing(app_and_client, worker_db):
    app, client = app_and_client
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    file_id = upload(client, class_id, "a.pdf", pdf("first version"))

    before = staged_files()
    queued = replace(client, file_id, "a-v2.pdf", pdf("too early"))
    assert queued.status_code == 409
    assert queued.json()["error"]["kind"] == "file_busy"
    assert staged_files() == before, "a refused replacement must not stage anything"

    assert tick(conn) is True
    assert replace(client, file_id, "a-v2.pdf", pdf("second version")).status_code == 202
    before = staged_files()
    again = replace(client, file_id, "a-v3.pdf", pdf("third version"))
    assert again.status_code == 409
    assert again.json()["error"]["kind"] == "file_busy"

    missing = replace(client, str(uuid.uuid4()), "x.pdf", pdf("x"))
    assert missing.status_code == 404
    assert missing.json() == client.get(f"/files/{uuid.uuid4()}").json()
    bad = replace(client, "not-a-uuid", "x.pdf", pdf("x"))
    assert bad.status_code == 400
    assert bad.json()["error"]["kind"] == "bad_file_id"

    app.dependency_overrides[owner_dep] = lambda: f"{owner_id}-someone-else"
    theirs = replace(client, file_id, "y.pdf", pdf("y"))
    assert theirs.status_code == 404
    assert theirs.json() == missing.json()
    assert staged_files() == before, "a refused replacement must not stage anything"


def test_a_transient_failure_keeps_the_replacement_pending_and_a_spent_budget_fails_it(
    app_and_client, worker_db, monkeypatch
):
    _, client = app_and_client
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    file_id = upload(client, class_id, "slides.pdf", pdf("the slides"))
    assert tick(conn) is True
    assert replace(client, file_id, "slides-v2.pdf", pdf("new slides")).status_code == 202

    assert tick(conn, FakeEmbeddings(transient_failures=1), max_attempts=1) is True
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["replacement"]) == ("ready", "pending")
    assert texts(conn, owner_id, class_id) == {"the slides"}

    assert tick(conn, FakeEmbeddings(), max_attempts=1) is True  # budget spent: not retried
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["replacement"]) == ("ready", "failed")
    assert body["replacement_failed_reason"] == "transient_exhausted"
    assert body["filename"] == "slides.pdf"
    assert texts(conn, owner_id, class_id) == {"the slides"}


# --- version history -----------------------------------------------------------------------


def versions(client, file_id):
    r = client.get(f"/files/{file_id}/versions")
    assert r.status_code == 200, r.text
    return [
        (v["version"], v["filename"], v["outcome"], v["failed_reason"], v["current"])
        for v in r.json()["versions"]
    ]


def test_every_upload_is_a_numbered_version_with_its_outcome(app_and_client, worker_db):
    app, client = app_and_client
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    file_id = upload(client, class_id, "week.pdf", pdf("version one"))
    assert versions(client, file_id) == [(1, "week.pdf", "pending", None, False)]
    assert tick(conn) is True
    assert versions(client, file_id) == [(1, "week.pdf", "published", None, True)]

    assert replace(client, file_id, "week-v2.pdf", CORRUPT).status_code == 202
    assert versions(client, file_id) == [
        (2, "week-v2.pdf", "pending", None, False),
        (1, "week.pdf", "published", None, True),
    ]
    assert tick(conn) is True
    assert versions(client, file_id) == [
        (2, "week-v2.pdf", "failed", "unparseable", False),
        (1, "week.pdf", "published", None, True),
    ]

    assert replace(client, file_id, "week-v3.pdf", pdf("version three")).status_code == 202
    assert tick(conn) is True
    assert versions(client, file_id) == [
        (3, "week-v3.pdf", "published", None, True),
        (2, "week-v2.pdf", "failed", "unparseable", False),
        (1, "week.pdf", "published", None, False),
    ]

    missing = client.get(f"/files/{uuid.uuid4()}/versions")
    assert missing.status_code == 404
    assert missing.json() == client.get(f"/files/{uuid.uuid4()}").json()
    assert client.get("/files/not-a-uuid/versions").json()["error"]["kind"] == "bad_file_id"
    app.dependency_overrides[owner_dep] = lambda: f"{owner_id}-someone-else"
    theirs = client.get(f"/files/{file_id}/versions")
    assert theirs.status_code == 404
    assert theirs.json() == missing.json()


@pytest.fixture
def old_schema_db(db):
    """A new database built from the applied migrations only, so rows exist before 0005 runs."""
    import psycopg
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    from gct.config import load_settings

    base = conninfo_to_dict(load_settings().database_url).get("dbname") or "postgres"
    name = f"{base}_t9_{uuid.uuid4().hex[:8]}"[:63]
    with psycopg.connect(load_settings().database_url, autocommit=True) as admin:
        admin.execute(f'create database "{name}"')
    params = conninfo_to_dict(load_settings().database_url)
    params["dbname"] = name
    url = make_conninfo(**params)
    root = Path(__file__).resolve().parents[2]
    try:
        with psycopg.connect(url, autocommit=True) as c:
            c.execute("create extension if not exists vector")
            for f in ("0001_init.sql", "0003_failed_reason_too_long.sql", "0004_one_worker.sql"):
                c.execute((root / "migrations" / f).read_text())
        yield url
    finally:
        with psycopg.connect(load_settings().database_url, autocommit=True) as admin:
            admin.execute(f'drop database if exists "{name}" with (force)')


def test_files_already_in_the_database_are_version_1(old_schema_db, monkeypatch):
    import os
    import subprocess
    import sys

    import psycopg

    owner = "t9-existing-owner"
    with psycopg.connect(old_schema_db, autocommit=True) as c:
        class_id = c.execute(
            "insert into classes (owner_id, name) values (%s, 'c') returning class_id::text",
            (owner,),
        ).fetchone()[0]
        ids = {}
        for name, status, reason in (
            ("done.pdf", "ready", None),
            ("bad.pdf", "failed", "unparseable"),
            ("waiting.pdf", "queued", None),
        ):
            ids[name] = c.execute(
                "insert into files "
                "(owner_id, class_id, filename, staging_ref, status, failed_reason) "
                "values (%s, %s::uuid, %s, %s, %s, %s) returning file_id::text",
                (owner, class_id, name, f"/staging/{name}", status, reason),
            ).fetchone()[0]

    root = Path(__file__).resolve().parents[2]
    env = {**os.environ, "DATABASE_URL": old_schema_db}
    for _ in range(2):
        out = subprocess.run(
            [sys.executable, "scripts/migrate.py"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
        )
        assert out.returncode == 0, out.stderr

    monkeypatch.setenv("DATABASE_URL", old_schema_db)
    app = create_app(embedder=FakeEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as client:
        assert versions(client, ids["done.pdf"]) == [(1, "done.pdf", "published", None, True)]
        assert versions(client, ids["bad.pdf"]) == [(1, "bad.pdf", "failed", "unparseable", False)]
        assert versions(client, ids["waiting.pdf"]) == [(1, "waiting.pdf", "pending", None, False)]


# --- restoring an earlier version (the last part; leans on every part before it) -------------


def restore(client, file_id, version):
    return client.post(f"/files/{file_id}/versions/{version}/restore")


def test_an_earlier_published_version_can_be_restored_as_the_next_version(
    app_and_client, worker_db
):
    app, client = app_and_client
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    file_id = upload(client, class_id, "a.pdf", pdf("text one"))
    assert tick(conn) is True
    assert replace(client, file_id, "b.pdf", pdf("text two")).status_code == 202
    assert tick(conn) is True
    assert replace(client, file_id, "c.pdf", CORRUPT).status_code == 202
    assert tick(conn) is True

    before = staged_files()
    r = restore(client, file_id, 1)
    assert r.status_code == 202, r.text
    assert r.json() == {"file_id": file_id, "filename": "a.pdf", "version": 4}
    assert staged_files() == before, "a restore reuses the staged bytes; it stages nothing"
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["replacement"], body["filename"]) == ("ready", "pending", "b.pdf")
    assert texts(conn, owner_id, class_id) == {"text two"}

    assert tick(conn) is True
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["replacement"], body["filename"]) == ("ready", None, "a.pdf")
    assert texts(conn, owner_id, class_id) == {"text one"}
    assert versions(client, file_id) == [
        (4, "a.pdf", "published", None, True),
        (3, "c.pdf", "failed", "unparseable", False),
        (2, "b.pdf", "published", None, False),
        (1, "a.pdf", "published", None, False),
    ]


def test_restore_refusals(app_and_client, worker_db):
    app, client = app_and_client
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    file_id = upload(client, class_id, "a.pdf", pdf("text one"))
    assert tick(conn) is True
    assert replace(client, file_id, "b.pdf", CORRUPT).status_code == 202
    assert tick(conn) is True  # version 2 failed; version 1 is current

    def kind(r):
        return r.status_code, r.json()["error"]["kind"]

    assert kind(restore(client, file_id, 2)) == (409, "version_not_published")
    assert kind(restore(client, file_id, 1)) == (409, "version_is_current")
    assert kind(restore(client, file_id, 9)) == (404, "version_not_found")
    assert kind(restore(client, "not-a-uuid", 1)) == (400, "bad_file_id")
    missing = restore(client, str(uuid.uuid4()), 1)
    assert missing.status_code == 404
    assert missing.json() == client.get(f"/files/{uuid.uuid4()}").json()

    assert replace(client, file_id, "c.pdf", pdf("text three")).status_code == 202
    assert tick(conn) is True  # version 3 is current now
    assert replace(client, file_id, "d.pdf", pdf("text four")).status_code == 202
    assert kind(restore(client, file_id, 1)) == (409, "file_busy")

    app.dependency_overrides[owner_dep] = lambda: f"{owner_id}-someone-else"
    theirs = restore(client, file_id, 1)
    assert theirs.status_code == 404
    assert theirs.json() == missing.json()
