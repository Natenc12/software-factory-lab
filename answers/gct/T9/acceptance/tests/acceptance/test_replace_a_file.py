"""Acceptance tests for the ticket: worked examples 1, 2, 3 and 6."""

from __future__ import annotations

import io
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.config import EMBEDDING_DIM
from gct.ingest.chunk import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from gct.jobs.worker import process_one
from gct.retriever.retrieve import retrieve


class FakeEmbeddings:
    model_id = "fake-embed-3"
    dim = EMBEDDING_DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[1.0] + [0.0] * (EMBEDDING_DIM - 1) for _ in texts]


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


@pytest.fixture
def client(worker_db):
    _, owner, _ = worker_db
    app = create_app(embedder=FakeEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def run_worker(conn):
    assert process_one(
        conn,
        embedder=FakeEmbeddings(),
        chunk_size=CHUNK_SIZE_WORDS,
        chunk_overlap=CHUNK_OVERLAP_WORDS,
    )


def upload(client, class_id, name, content):
    r = client.post("/files", data={"class_id": class_id}, files={"file": (name, content)})
    assert r.status_code == 202, r.text
    return r.json()["file_id"]


def texts(conn, owner, class_id):
    return {c.text for c in retrieve(conn, "q", owner, class_id, embedder=FakeEmbeddings(), k=20)}


def test_examples_1_2_3_replace_a_ready_file(client, worker_db, db_other):
    conn, owner, class_id = worker_db
    conn.autocommit = True
    file_id = upload(client, class_id, "week-1.pdf", pdf("the old lecture text"))
    run_worker(conn)

    r = client.put(
        f"/files/{file_id}", files={"file": ("week-1-v2.pdf", pdf("the new lecture text"))}
    )
    assert r.status_code == 202
    assert r.json() == {"file_id": file_id, "filename": "week-1-v2.pdf"}

    body = client.get(f"/files/{file_id}").json()
    assert body["status"] == "ready"
    assert body["replacement"] == "pending"
    assert body["replacement_failed_reason"] is None
    assert body["filename"] == "week-1.pdf"
    assert texts(conn, owner, class_id) == {"the old lecture text"}

    run_worker(conn)
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["replacement"], body["filename"]) == (
        "ready",
        None,
        "week-1-v2.pdf",
    )
    assert texts(conn, owner, class_id) == {"the new lecture text"}
    ref = db_other.execute(
        "select staging_ref from files where file_id = %s::uuid", (file_id,)
    ).fetchone()[0]
    assert Path(ref).name == "week-1-v2.pdf"


def test_example_6_replace_a_failed_file(client, worker_db):
    conn, owner, class_id = worker_db
    conn.autocommit = True
    file_id = upload(client, class_id, "broken.pdf", b"%PDF-1.7\nnot a pdf\n")
    run_worker(conn)
    assert (
        client.put(f"/files/{file_id}", files={"file": ("fixed.pdf", pdf("ok now"))}).status_code
        == 202
    )
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["failed_reason"], body["replacement"]) == ("queued", None, None)
    run_worker(conn)
    body = client.get(f"/files/{file_id}").json()
    assert (body["status"], body["filename"]) == ("ready", "fixed.pdf")
