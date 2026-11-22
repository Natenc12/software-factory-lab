"""Acceptance tests for the ticket: the end state of worked examples 1 and 3."""

from __future__ import annotations

import io

from reportlab.pdfgen import canvas

from gct.config import EMBEDDING_DIM
from gct.ingest.chunk import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from gct.jobs import worker
from gct.jobs.queue import enqueue
from gct.jobs.worker import process_one
from gct.providers.base import TransientEmbeddingError


class FlakyEmbeddings:
    model_id = "fake-embed-3"

    def __init__(self, failures: int) -> None:
        self.calls = 0
        self.failures = failures

    def embed(self, texts):
        self.calls += 1
        if self.calls <= self.failures:
            raise TransientEmbeddingError("simulated provider 429")
        return [[1.0] + [0.0] * (EMBEDDING_DIM - 1) for _ in texts]


def write_pdf(path, text):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(612, 792))
    c.drawString(72, 700, text)
    c.showPage()
    c.save()
    path.write_bytes(buf.getvalue())
    return path


def status(db_other, file_id):
    return db_other.execute(
        "select status, failed_reason from files where file_id = %s::uuid", (file_id,)
    ).fetchone()


def run_until_settled(conn, embedder, db_other, file_id, limit=5):
    for _ in range(limit):
        process_one(
            conn, embedder=embedder, chunk_size=CHUNK_SIZE_WORDS, chunk_overlap=CHUNK_OVERLAP_WORDS
        )
        if status(db_other, file_id)[0] in ("ready", "failed"):
            return


def test_example_1_one_429_then_success_ends_ready(worker_db, db_other, tmp_path, monkeypatch):
    conn, owner, class_id = worker_db
    conn.autocommit = True
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    file_id = enqueue(
        conn, path=write_pdf(tmp_path / "a.pdf", "x"), owner_id=owner, class_id=class_id
    )
    run_until_settled(conn, FlakyEmbeddings(failures=1), db_other, file_id)
    assert status(db_other, file_id) == ("ready", None)


def test_example_3_a_corrupt_file_fails_at_once(worker_db, db_other, tmp_path, monkeypatch):
    conn, owner, class_id = worker_db
    conn.autocommit = True
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"%PDF-1.7\nnot a pdf\n")
    file_id = enqueue(conn, path=path, owner_id=owner, class_id=class_id)
    embedder = FlakyEmbeddings(failures=0)
    process_one(
        conn, embedder=embedder, chunk_size=CHUNK_SIZE_WORDS, chunk_overlap=CHUNK_OVERLAP_WORDS
    )
    assert status(db_other, file_id) == ("failed", "unparseable")
    assert embedder.calls == 0
