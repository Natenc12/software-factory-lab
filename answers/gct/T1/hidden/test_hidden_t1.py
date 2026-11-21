"""Hidden tests for T1: the `files` row must describe the attempt and the chunk set it publishes.

Adapted from the tests that came with the real fix. Every assertion about what was published is read
through `db_other`, a second connection, so it holds only for committed work.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import psycopg
import pytest
from reportlab.pdfgen import canvas

from gct.config import EMBEDDING_DIM
from gct.ingest.chunk import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from gct.ingest.index import index_file
from gct.ingest.parse import ParseError
from gct.ingest.pipeline import PreparedChunk
from gct.jobs import worker
from gct.jobs.queue import enqueue
from gct.jobs.worker import backoff_seconds, process_one
from gct.providers.base import TransientEmbeddingError

MODEL_ID = "fake-embed-3"


# --- helpers -----------------------------------------------------------------------------------


class FakeEmbeddings:
    model_id = MODEL_ID

    def __init__(self, transient_failures: int = 0) -> None:
        self.calls: list[list[str]] = []
        self._failures_left = transient_failures

    def embed(self, texts):
        texts = list(texts)
        self.calls.append(texts)
        if self._failures_left > 0:
            self._failures_left -= 1
            raise TransientEmbeddingError("simulated provider 429 - slow down")
        return [[float((hash(t) % 97) + 1)] + [0.0] * (EMBEDDING_DIM - 1) for t in texts]


def write_corrupt_pdf(path: Path) -> Path:
    path.write_bytes(b"%PDF-1.7\nthis is not a PDF at all\n")
    return path


def write_pdf(path: Path, page_texts: list[str]) -> Path:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(612, 792))
    for text in page_texts:
        c.drawString(72, 700, text)
        c.showPage()
    c.save()
    path.write_bytes(buf.getvalue())
    return path


def tick(conn, embedder, **overrides):
    return process_one(
        conn,
        embedder=embedder,
        chunk_size=CHUNK_SIZE_WORDS,
        chunk_overlap=CHUNK_OVERLAP_WORDS,
        **overrides,
    )


def _chunk(owner_id, class_id, text, page, file="lecture.pdf") -> PreparedChunk:
    return PreparedChunk(
        text=text,
        file=file,
        page_or_slide=page,
        embedding=[0.0] * EMBEDDING_DIM,
        owner_id=owner_id,
        class_id=class_id,
        embedding_model_id=MODEL_ID,
    )


def _seed_class(conn, owner_id: str) -> str:
    class_id = str(uuid.uuid4())
    conn.execute(
        "insert into classes (class_id, owner_id, name) values (%s::uuid, %s, %s)",
        (class_id, owner_id, "another class"),
    )
    return class_id


def _purge(conn, owner_id: str, file_id: str | None = None) -> None:
    """Delete rows the fixture's teardown cannot reach (it deletes by the fixture's owner only)."""
    if file_id is not None:
        conn.execute("delete from chunks where file_id = %s::uuid", (file_id,))
        conn.execute("delete from jobs where file_id = %s::uuid", (file_id,))
        conn.execute("delete from files where file_id = %s::uuid", (file_id,))
    conn.execute("delete from chunks where owner_id = %s", (owner_id,))
    conn.execute("delete from files where owner_id = %s", (owner_id,))
    conn.execute("delete from classes where owner_id = %s", (owner_id,))


def _file_row(db_other, file_id: str) -> tuple:
    return db_other.execute(
        "select status, failed_reason from files where file_id = %s::uuid", (file_id,)
    ).fetchone()


def _half_bury(conn, monkeypatch, *, source, owner_id, class_id) -> str:
    """Leave `files` at ('failed', reason) while the job stays claimable.

    Interrupt the terminal-failure path between its `files` write and its `jobs` write, then
    disarm, so the caller's next tick runs normally.
    """
    real_fail = worker.fail
    armed = {"on": True}

    def fail_or_interrupt(*args, **kwargs):
        if armed["on"]:
            raise KeyboardInterrupt("interrupt between the files write and the jobs write")
        return real_fail(*args, **kwargs)

    monkeypatch.setattr(worker, "fail", fail_or_interrupt)
    file_id = enqueue(conn, path=source, owner_id=owner_id, class_id=class_id)
    with pytest.raises(KeyboardInterrupt):
        tick(conn, FakeEmbeddings())
    armed["on"] = False
    return file_id


# --- re-index under a different scope ----------------------------------------------------------


def test_reindex_refreshes_filename_owner_and_class_from_the_incoming_call(db, db_other):
    conn, owner_a, class_a = db
    conn.autocommit = True
    owner_b = f"test-owner-{uuid.uuid4()}"
    class_b = _seed_class(conn, owner_b)
    file_id = str(uuid.uuid4())
    try:
        index_file(
            conn,
            file_id=file_id,
            filename="old.pdf",
            owner_id=owner_a,
            class_id=class_a,
            chunks=[_chunk(owner_a, class_a, "the old passage", 1, file="old.pdf")],
        )
        index_file(
            conn,
            file_id=file_id,
            filename="new.pdf",
            owner_id=owner_b,
            class_id=class_b,
            chunks=[_chunk(owner_b, class_b, "the new passage", 1, file="new.pdf")],
        )
        files_row = db_other.execute(
            "select owner_id, class_id::text, filename from files where file_id = %s::uuid",
            (file_id,),
        ).fetchone()
        assert files_row == (owner_b, class_b, "new.pdf")
        chunk_scopes = db_other.execute(
            "select distinct owner_id, class_id::text, file from chunks where file_id = %s::uuid",
            (file_id,),
        ).fetchall()
        assert chunk_scopes == [files_row]
    finally:
        _purge(conn, owner_b, file_id)


@pytest.mark.parametrize("varying", ["filename", "owner_id", "class_id"])
def test_each_scope_column_is_refreshed_on_its_own(db, db_other, varying):
    conn, owner_a, class_a = db
    conn.autocommit = True
    file_id = str(uuid.uuid4())
    second = {"filename": "old.pdf", "owner_id": owner_a, "class_id": class_a}
    if varying == "owner_id":
        second["owner_id"] = f"test-owner-{uuid.uuid4()}"
    elif varying == "class_id":
        second["class_id"] = _seed_class(conn, owner_a)
    else:
        second["filename"] = "renamed.pdf"
    try:
        index_file(
            conn,
            file_id=file_id,
            filename="old.pdf",
            owner_id=owner_a,
            class_id=class_a,
            chunks=[_chunk(owner_a, class_a, "the old passage", 1, file="old.pdf")],
        )
        new_chunk = _chunk(
            second["owner_id"], second["class_id"], "new", 1, file=second["filename"]
        )
        index_file(conn, file_id=file_id, chunks=[new_chunk], **second)
        published = db_other.execute(
            "select owner_id, class_id::text, filename from files where file_id = %s::uuid",
            (file_id,),
        ).fetchone()
        assert published == (second["owner_id"], second["class_id"], second["filename"])
    finally:
        _purge(conn, second["owner_id"], file_id)


def test_reindex_into_a_class_that_does_not_exist_is_refused_and_changes_nothing(db, db_other):
    conn, owner_id, class_id = db
    conn.autocommit = True
    file_id = str(uuid.uuid4())
    ghost_class = str(uuid.uuid4())  # never seeded
    index_file(
        conn,
        file_id=file_id,
        filename="old.pdf",
        owner_id=owner_id,
        class_id=class_id,
        chunks=[
            _chunk(owner_id, class_id, "old-A", 1, file="old.pdf"),
            _chunk(owner_id, class_id, "old-B", 2, file="old.pdf"),
        ],
    )
    with pytest.raises((psycopg.Error, ValueError)):
        index_file(
            conn,
            file_id=file_id,
            filename="new.pdf",
            owner_id=owner_id,
            class_id=ghost_class,
            chunks=[_chunk(owner_id, ghost_class, "new-A", 1, file="new.pdf")],
        )
    if conn.info.transaction_status != psycopg.pq.TransactionStatus.IDLE:
        conn.rollback()
    assert db_other.execute(
        "select owner_id, class_id::text, filename, status from files where file_id = %s::uuid",
        (file_id,),
    ).fetchone() == (owner_id, class_id, "old.pdf", "ready")
    chunks = db_other.execute(
        "select text, class_id::text from chunks where file_id = %s::uuid order by text",
        (file_id,),
    ).fetchall()
    assert chunks == [("old-A", class_id), ("old-B", class_id)]


# --- a new attempt must not carry the previous attempt's failure reason ------------------------


def test_a_retried_file_shows_no_old_reason_while_it_is_being_worked_on(
    db, db_other, tmp_path, monkeypatch
):
    """The retry here fails transiently, so nothing after the pick-up publishes anything."""
    conn, owner_id, class_id = db
    conn.autocommit = True
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)

    # First: a row that is already `ready` is left exactly as it is by a pick-up of its job.
    other = write_corrupt_pdf(tmp_path / "already-published.pdf")
    ready_id = enqueue(conn, path=other, owner_id=owner_id, class_id=class_id)
    conn.execute(
        "update files set status = 'ready', failed_reason = 'unparseable' where file_id = %s::uuid",
        (ready_id,),
    )
    assert tick(conn, FakeEmbeddings()) is True
    assert _file_row(db_other, ready_id) == ("ready", "unparseable")

    # Then: a half-buried file picked up again shows `processing` and no reason.
    source = write_corrupt_pdf(tmp_path / "half-buried.pdf")
    file_id = _half_bury(conn, monkeypatch, source=source, owner_id=owner_id, class_id=class_id)
    assert _file_row(db_other, file_id) == ("failed", "unparseable")
    assert db_other.execute(
        "select state from jobs where file_id = %s::uuid", (file_id,)
    ).fetchone() == ("queued",)

    def transient(*_args, **_kwargs):
        raise TransientEmbeddingError("simulated provider 429")

    monkeypatch.setattr(worker, "ingest_file", transient)
    assert tick(conn, FakeEmbeddings()) is True
    assert _file_row(db_other, file_id) == ("processing", None)


def test_a_retry_that_succeeds_leaves_no_reason_and_keeps_the_job_error_trail(
    db, db_other, tmp_path, monkeypatch
):
    conn, owner_id, class_id = db
    conn.autocommit = True
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    source = write_corrupt_pdf(tmp_path / "arrived-late.pdf")
    file_id = _half_bury(conn, monkeypatch, source=source, owner_id=owner_id, class_id=class_id)
    assert _file_row(db_other, file_id) == ("failed", "unparseable")
    (first_error,) = db_other.execute(
        "select last_error from jobs where file_id = %s::uuid", (file_id,)
    ).fetchone()
    assert first_error

    write_pdf(source, ["the real lecture text finally arrived at the staging path"])
    assert tick(conn, FakeEmbeddings()) is True

    status, reason, state, last_error, chunk_count = db_other.execute(
        """
        select f.status, f.failed_reason, j.state, j.last_error,
               (select count(*) from chunks c where c.file_id = f.file_id)
        from files f join jobs j using (file_id) where f.file_id = %s::uuid
        """,
        (file_id,),
    ).fetchone()
    assert (status, reason) == ("ready", None)
    assert state == "done"
    assert chunk_count > 0
    assert last_error == first_error, "the job's record of the earlier attempt must survive"


def test_a_second_terminal_failure_reports_the_new_reason_and_never_the_old_one_midway(
    db, db_other, tmp_path, monkeypatch
):
    conn, owner_id, class_id = db
    conn.autocommit = True
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    source = write_corrupt_pdf(tmp_path / "fails-twice.pdf")
    file_id = _half_bury(conn, monkeypatch, source=source, owner_id=owner_id, class_id=class_id)
    assert _file_row(db_other, file_id) == ("failed", "unparseable")
    seen: list[tuple] = []

    def empty_after_looking(*_args, **_kwargs):
        seen.append(_file_row(db_other, file_id))
        raise ParseError("empty", "the file parsed but contained no extractable text")

    monkeypatch.setattr(worker, "ingest_file", empty_after_looking)
    assert tick(conn, FakeEmbeddings()) is True
    assert seen == [("processing", None)]
    assert _file_row(db_other, file_id) == ("failed", "empty")


def test_a_real_transient_failure_after_a_half_bury_leaves_processing_with_no_reason(
    db, db_other, tmp_path, monkeypatch
):
    conn, owner_id, class_id = db
    conn.autocommit = True
    slept: list[float] = []
    monkeypatch.setattr(worker.time, "sleep", slept.append)
    source = write_corrupt_pdf(tmp_path / "then-a-429.pdf")
    file_id = _half_bury(conn, monkeypatch, source=source, owner_id=owner_id, class_id=class_id)
    assert _file_row(db_other, file_id) == ("failed", "unparseable")
    slept.clear()

    write_pdf(source, ["a page the provider refuses exactly once"])
    embedder = FakeEmbeddings(transient_failures=1)
    assert tick(conn, embedder) is True

    assert _file_row(db_other, file_id) == ("processing", None)
    state, attempts = db_other.execute(
        "select state, attempts from jobs where file_id = %s::uuid", (file_id,)
    ).fetchone()
    assert (state, attempts) == ("queued", 2)
    assert len(embedder.calls) == 1
    assert slept == [backoff_seconds(2)]
