"""Acceptance tests for the ticket: worked examples 1, 3 and 4.

Every assertion about what was published is read through `db_other`, a second connection.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from gct.config import EMBEDDING_DIM
from gct.ingest.chunk import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from gct.ingest.index import index_file
from gct.ingest.pipeline import PreparedChunk
from gct.jobs import worker
from gct.jobs.queue import enqueue
from gct.jobs.worker import process_one
from gct.providers.base import TransientEmbeddingError


class FakeEmbeddings:
    model_id = "fake-embed-3"

    def __init__(self, transient_failures: int = 0) -> None:
        self.calls: list[list[str]] = []
        self._failures_left = transient_failures

    def embed(self, texts):
        texts = list(texts)
        self.calls.append(texts)
        if self._failures_left > 0:
            self._failures_left -= 1
            raise TransientEmbeddingError("simulated provider 429")
        return [[1.0] + [0.0] * (EMBEDDING_DIM - 1) for _ in texts]


def write_pdf(path: Path, page_texts: list[str]) -> Path:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(612, 792))
    for text in page_texts:
        c.drawString(72, 700, text)
        c.showPage()
    c.save()
    path.write_bytes(buf.getvalue())
    return path


def tick(conn, embedder):
    return process_one(
        conn,
        embedder=embedder,
        chunk_size=CHUNK_SIZE_WORDS,
        chunk_overlap=CHUNK_OVERLAP_WORDS,
    )


def chunk(owner_id, class_id, text, file) -> PreparedChunk:
    return PreparedChunk(
        text=text,
        file=file,
        page_or_slide=1,
        embedding=[0.0] * EMBEDDING_DIM,
        owner_id=owner_id,
        class_id=class_id,
        embedding_model_id="fake-embed-3",
    )


def interrupted_failure(conn, monkeypatch, tmp_path, owner_id, class_id):
    """A file whose previous attempt wrote ('failed', 'unparseable') but left the job queued."""
    source = tmp_path / "upload.pdf"
    source.write_bytes(b"%PDF-1.7\nnot a pdf\n")
    real_fail = worker.fail

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt("interrupted between the files write and the jobs write")

    monkeypatch.setattr(worker, "fail", interrupt)
    file_id = enqueue(conn, path=source, owner_id=owner_id, class_id=class_id)
    with pytest.raises(KeyboardInterrupt):
        tick(conn, FakeEmbeddings())
    monkeypatch.setattr(worker, "fail", real_fail)
    return file_id, source


def status_row(db_other, file_id):
    return db_other.execute(
        "select status, failed_reason from files where file_id = %s::uuid", (file_id,)
    ).fetchone()


def test_example_1_reindex_takes_filename_owner_and_class_from_the_call(db, db_other):
    conn, owner_a, class_a = db
    conn.autocommit = True
    owner_b = f"test-owner-{uuid.uuid4()}"
    class_b = str(uuid.uuid4())
    conn.execute(
        "insert into classes (class_id, owner_id, name) values (%s::uuid, %s, 'class Y')",
        (class_b, owner_b),
    )
    file_id = str(uuid.uuid4())
    try:
        index_file(
            conn,
            file_id=file_id,
            filename="old.pdf",
            owner_id=owner_a,
            class_id=class_a,
            chunks=[chunk(owner_a, class_a, "old passage", "old.pdf")],
        )
        index_file(
            conn,
            file_id=file_id,
            filename="new.pdf",
            owner_id=owner_b,
            class_id=class_b,
            chunks=[chunk(owner_b, class_b, "new passage", "new.pdf")],
        )
        row = db_other.execute(
            "select status, filename, owner_id, class_id::text from files where file_id = %s::uuid",
            (file_id,),
        ).fetchone()
        assert row == ("ready", "new.pdf", owner_b, class_b)
        chunks = db_other.execute(
            "select distinct file, owner_id, class_id::text from chunks where file_id = %s::uuid",
            (file_id,),
        ).fetchall()
        assert chunks == [("new.pdf", owner_b, class_b)]
    finally:
        conn.execute("delete from chunks where file_id = %s::uuid", (file_id,))
        conn.execute("delete from files where file_id = %s::uuid", (file_id,))
        conn.execute("delete from classes where owner_id = %s", (owner_b,))


def test_example_3_a_transient_retry_shows_processing_and_no_reason(
    db, db_other, tmp_path, monkeypatch
):
    conn, owner_id, class_id = db
    conn.autocommit = True
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    file_id, source = interrupted_failure(conn, monkeypatch, tmp_path, owner_id, class_id)
    assert status_row(db_other, file_id) == ("failed", "unparseable")

    write_pdf(source, ["a page the provider refuses once"])
    assert tick(conn, FakeEmbeddings(transient_failures=1)) is True

    assert status_row(db_other, file_id) == ("processing", None)
    assert db_other.execute(
        "select state, attempts from jobs where file_id = %s::uuid", (file_id,)
    ).fetchone() == ("queued", 2)


def test_example_4_a_successful_retry_is_ready_with_no_reason(db, db_other, tmp_path, monkeypatch):
    conn, owner_id, class_id = db
    conn.autocommit = True
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    file_id, source = interrupted_failure(conn, monkeypatch, tmp_path, owner_id, class_id)
    (first_error,) = db_other.execute(
        "select last_error from jobs where file_id = %s::uuid", (file_id,)
    ).fetchone()

    write_pdf(source, ["the real lecture text"])
    assert tick(conn, FakeEmbeddings()) is True

    assert status_row(db_other, file_id) == ("ready", None)
    state, last_error, n_chunks = db_other.execute(
        """
        select j.state, j.last_error, (select count(*) from chunks c where c.file_id = j.file_id)
        from jobs j where j.file_id = %s::uuid
        """,
        (file_id,),
    ).fetchone()
    assert state == "done"
    assert n_chunks > 0
    assert last_error == first_error
