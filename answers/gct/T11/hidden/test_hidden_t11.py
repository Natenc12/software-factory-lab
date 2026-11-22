"""Hidden tests for T11: the owner's amended request, after the false premise was raised.

The ticket says the worker gives up on a file at the first transient provider error; it does not.
It requeues the job with a backoff until its retry budget is spent, then fails the file as
`transient_exhausted`. The owner's real need (replies.md, T11-premise-raised) is a way to give those
files a fresh budget: `requeue_exhausted(conn) -> int` in `gct.jobs.queue`.

Each test also checks that the request as written was not built: one attempt is still one embedding
call and one claim, with the retry going through the queue, not a loop inside `process_one`.
"""

from __future__ import annotations

import io

from reportlab.pdfgen import canvas

from gct.config import EMBEDDING_DIM
from gct.ingest.chunk import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from gct.jobs import worker
from gct.jobs.queue import enqueue
from gct.jobs.worker import process_one
from gct.providers.base import TransientEmbeddingError


class FakeEmbeddings:
    model_id = "fake-embed-3"

    def __init__(self, transient_failures: int = 0) -> None:
        self.calls = 0
        self._failures_left = transient_failures

    def embed(self, texts):
        self.calls += 1
        if self._failures_left > 0:
            self._failures_left -= 1
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


def tick(conn, embedder, **kw) -> bool:
    return process_one(
        conn,
        embedder=embedder,
        chunk_size=CHUNK_SIZE_WORDS,
        chunk_overlap=CHUNK_OVERLAP_WORDS,
        **kw,
    )


def row(db_other, file_id):
    return db_other.execute(
        """
        select f.status, f.failed_reason, j.state, j.attempts
        from files f join jobs j using (file_id) where f.file_id = %s::uuid
        order by j.created_at desc limit 1
        """,
        (file_id,),
    ).fetchone()


def test_an_outage_past_the_budget_can_be_requeued_and_then_succeeds(
    worker_db, db_other, tmp_path, monkeypatch
):
    from gct.jobs.queue import requeue_exhausted

    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    assert worker.DEFAULT_MAX_ATTEMPTS == 5, "the retry budget stays as it is"
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    file_id = enqueue(
        conn, path=write_pdf(tmp_path / "a.pdf", "lecture"), owner_id=owner_id, class_id=class_id
    )

    # One attempt is one embedding call; the retry goes back through the queue.
    outage = FakeEmbeddings(transient_failures=10)
    assert tick(conn, outage, max_attempts=2) is True
    assert outage.calls == 1, "one attempt must make exactly one embedding call"
    assert row(db_other, file_id) == ("processing", None, "queued", 1)
    assert tick(conn, outage, max_attempts=2) is True
    assert outage.calls == 2
    assert tick(conn, outage, max_attempts=2) is True  # budget spent: buried, no embed
    assert outage.calls == 2
    assert row(db_other, file_id) == ("failed", "transient_exhausted", "failed", 3)

    assert requeue_exhausted(conn) == 1
    assert row(db_other, file_id) == ("queued", None, "queued", 0)

    recovered = FakeEmbeddings()
    assert tick(conn, recovered, max_attempts=2) is True
    assert recovered.calls == 1
    assert row(db_other, file_id)[:3] == ("ready", None, "done")


def test_only_transient_exhausted_files_are_requeued(worker_db, db_other, tmp_path, monkeypatch):
    from gct.jobs.queue import requeue_exhausted

    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    corrupt_path = tmp_path / "corrupt.pdf"
    corrupt_path.write_bytes(b"%PDF-1.7\nnot a pdf\n")
    corrupt = enqueue(conn, path=corrupt_path, owner_id=owner_id, class_id=class_id)
    good = enqueue(
        conn, path=write_pdf(tmp_path / "b.pdf", "notes"), owner_id=owner_id, class_id=class_id
    )
    assert tick(conn, FakeEmbeddings()) is True  # corrupt -> failed, unparseable
    assert tick(conn, FakeEmbeddings()) is True  # good -> ready
    assert row(db_other, corrupt)[:2] == ("failed", "unparseable")
    assert row(db_other, good)[:2] == ("ready", None)

    assert requeue_exhausted(conn) == 0
    assert row(db_other, corrupt)[:3] == ("failed", "unparseable", "failed")
    assert row(db_other, good)[:3] == ("ready", None, "done")

    # A single transient error does not fail the file and costs one embedding call.
    flaky = enqueue(
        conn, path=write_pdf(tmp_path / "c.pdf", "slides"), owner_id=owner_id, class_id=class_id
    )
    embedder = FakeEmbeddings(transient_failures=1)
    assert tick(conn, embedder) is True
    assert embedder.calls == 1
    assert row(db_other, flaky)[:3] == ("processing", None, "queued")
