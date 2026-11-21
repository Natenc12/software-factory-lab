"""Hidden tests for T4: deleting an uploaded file, through the library and through the API."""

from __future__ import annotations

import io
import uuid
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.config import EMBEDDING_DIM
from gct.files import get_file_status
from gct.ingest.chunk import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from gct.ingest.index import index_file
from gct.ingest.pipeline import PreparedChunk
from gct.jobs.queue import enqueue
from gct.jobs.worker import process_one
from gct.retriever.retrieve import retrieve
from gct.staging import stage

VEC = [0.0] * (EMBEDDING_DIM - 1) + [1.0]


class FakeEmbeddings:
    model_id = "fake-embed-3"
    dim = EMBEDDING_DIM

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [list(VEC) for _ in texts]


class StubGeneration:
    model_id = "stub-gen"

    def generate(self, messages) -> str:
        return ""


def _upload(conn, owner_id, class_id, tmp_path, name, *, ready=True) -> tuple[str, Path]:
    """Stage bytes the way POST /files does, enqueue them, and optionally publish chunks."""
    staged = Path(stage(io.BytesIO(b"%PDF-1.7 bytes"), filename=name, staging_dir=tmp_path))
    file_id = enqueue(conn, path=str(staged), owner_id=owner_id, class_id=class_id)
    if ready:
        index_file(
            conn,
            file_id=file_id,
            filename=name,
            owner_id=owner_id,
            class_id=class_id,
            chunks=[
                PreparedChunk(
                    text=f"{name} passage {i}",
                    file=name,
                    page_or_slide=i + 1,
                    embedding=list(VEC),
                    owner_id=owner_id,
                    class_id=class_id,
                    embedding_model_id="fake-embed-3",
                )
                for i in range(2)
            ],
        )
        conn.execute("update jobs set state = 'done' where file_id = %s::uuid", (file_id,))
    return file_id, staged


def _counts(db_other, file_id) -> tuple[int, int, int]:
    return tuple(
        db_other.execute(
            f"select count(*) from {table} where file_id = %s::uuid", (file_id,)
        ).fetchone()[0]
        for table in ("files", "chunks", "jobs")
    )


def test_deleting_a_ready_file_removes_its_rows_and_bytes_and_nothing_else(db, db_other, tmp_path):
    from gct.files import delete_file

    conn, owner_id, class_id = db
    conn.autocommit = True
    gone, gone_path = _upload(conn, owner_id, class_id, tmp_path, "week-1.pdf")
    kept, kept_path = _upload(conn, owner_id, class_id, tmp_path, "week-2.pdf")
    assert _counts(db_other, gone) == (1, 2, 1)

    assert delete_file(conn, file_id=gone, owner_id=owner_id) is True

    assert _counts(db_other, gone) == (0, 0, 0)
    assert _counts(db_other, kept) == (1, 2, 1)
    assert not gone_path.exists()
    assert kept_path.exists()
    assert get_file_status(conn, file_id=gone, owner_id=owner_id) is None
    got = retrieve(conn, "anything", owner_id, class_id, embedder=FakeEmbeddings(), k=10)
    assert {c.file for c in got} == {"week-2.pdf"}


def test_delete_is_scoped_to_the_owner_and_reports_a_missing_file(db, db_other, tmp_path):
    from gct.files import delete_file

    conn, owner_id, class_id = db
    conn.autocommit = True
    file_id, staged = _upload(conn, owner_id, class_id, tmp_path, "notes.pdf")

    assert delete_file(conn, file_id=file_id, owner_id="someone-else") is False
    assert delete_file(conn, file_id=str(uuid.uuid4()), owner_id=owner_id) is False
    assert _counts(db_other, file_id) == (1, 2, 1)
    assert staged.exists()
    with pytest.raises(ValueError):
        delete_file(conn, file_id="not-a-file-id", owner_id=owner_id)
    # Any spelling of the id the library accepts elsewhere works here too.
    assert delete_file(conn, file_id=uuid.UUID(file_id).urn, owner_id=owner_id) is True
    assert _counts(db_other, file_id) == (0, 0, 0)


def test_a_file_the_worker_is_on_cannot_be_deleted(db, db_other, tmp_path):
    from gct.files import FileBusy, delete_file

    conn, owner_id, class_id = db
    conn.autocommit = True

    # The file row says processing.
    first, first_path = _upload(conn, owner_id, class_id, tmp_path, "a.pdf", ready=False)
    conn.execute("update files set status = 'processing' where file_id = %s::uuid", (first,))
    with pytest.raises(FileBusy):
        delete_file(conn, file_id=first, owner_id=owner_id)
    assert _counts(db_other, first) == (1, 0, 1)
    assert first_path.exists()

    # The job has been claimed but the file row has not been moved to processing yet.
    second, second_path = _upload(conn, owner_id, class_id, tmp_path, "b.pdf", ready=False)
    conn.execute("update jobs set state = 'processing' where file_id = %s::uuid", (second,))
    assert get_file_status(conn, file_id=second, owner_id=owner_id).status == "queued"
    with pytest.raises(FileBusy):
        delete_file(conn, file_id=second, owner_id=owner_id)
    assert _counts(db_other, second) == (1, 0, 1)
    assert second_path.exists()


def test_a_queued_file_can_be_deleted_and_is_then_never_processed(worker_db, db_other, tmp_path):
    from gct.files import delete_file

    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    file_id, staged = _upload(conn, owner_id, class_id, tmp_path, "queued.pdf", ready=False)
    assert delete_file(conn, file_id=file_id, owner_id=owner_id) is True
    assert _counts(db_other, file_id) == (0, 0, 0)
    assert not staged.exists()

    embedder = FakeEmbeddings()
    ran = process_one(
        conn, embedder=embedder, chunk_size=CHUNK_SIZE_WORDS, chunk_overlap=CHUNK_OVERLAP_WORDS
    )
    assert ran is False, "the worker found a job for a deleted file"
    assert embedder.calls == []


def test_missing_staged_bytes_do_not_stop_a_delete(db, db_other, tmp_path):
    from gct.files import delete_file

    conn, owner_id, class_id = db
    conn.autocommit = True
    file_id, staged = _upload(conn, owner_id, class_id, tmp_path, "vanished.pdf")
    staged.unlink()
    assert delete_file(conn, file_id=file_id, owner_id=owner_id) is True
    assert _counts(db_other, file_id) == (0, 0, 0)


@pytest.fixture
def client(db):
    _, owner, _ = db
    app = create_app(embedder=FakeEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c, app


def test_the_delete_route(client, db, db_other, tmp_path):
    http, app = client
    conn, owner_id, class_id = db
    conn.autocommit = True
    file_id, staged = _upload(conn, owner_id, class_id, tmp_path, "route.pdf")

    response = http.delete(f"/files/{file_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert _counts(db_other, file_id) == (0, 0, 0)
    assert not staged.exists()

    again = http.delete(f"/files/{file_id}")
    assert again.status_code == 404
    assert again.json()["error"]["kind"] == "file_not_found"
    assert http.get(f"/files/{file_id}").status_code == 404

    bad = http.delete("/files/not-a-uuid")
    assert bad.status_code == 400
    assert bad.json()["error"]["kind"] == "bad_file_id"

    busy, _ = _upload(conn, owner_id, class_id, tmp_path, "busy.pdf", ready=False)
    conn.execute("update files set status = 'processing' where file_id = %s::uuid", (busy,))
    response = http.delete(f"/files/{busy}")
    assert response.status_code == 409
    assert response.json()["error"]["kind"] == "file_busy"

    theirs, theirs_path = _upload(conn, owner_id, class_id, tmp_path, "theirs.pdf")
    app.dependency_overrides[owner_dep] = lambda: "someone-else"
    response = http.delete(f"/files/{theirs}")
    assert response.status_code == 404
    assert response.json()["error"]["kind"] == "file_not_found"
    assert _counts(db_other, theirs) == (1, 2, 1)
    assert theirs_path.exists()
