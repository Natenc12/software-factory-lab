"""Acceptance tests for the ticket: worked examples 1, 2, 5 and 8."""

from __future__ import annotations

import io
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.config import EMBEDDING_DIM
from gct.files import delete_file, get_file_status
from gct.ingest.index import index_file
from gct.ingest.pipeline import PreparedChunk
from gct.jobs.queue import enqueue
from gct.retriever.retrieve import retrieve
from gct.staging import stage

VEC = [0.0] * (EMBEDDING_DIM - 1) + [1.0]


class FakeEmbeddings:
    model_id = "fake-embed-3"

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [list(VEC) for _ in texts]


class StubGeneration:
    model_id = "stub-gen"

    def generate(self, messages) -> str:
        return ""


def ready_file(conn, owner_id, class_id, tmp_path, name):
    staged = Path(stage(io.BytesIO(b"bytes"), filename=name, staging_dir=tmp_path))
    file_id = enqueue(conn, path=str(staged), owner_id=owner_id, class_id=class_id)
    index_file(
        conn,
        file_id=file_id,
        filename=name,
        owner_id=owner_id,
        class_id=class_id,
        chunks=[
            PreparedChunk(
                text=f"{name} text",
                file=name,
                page_or_slide=1,
                embedding=list(VEC),
                owner_id=owner_id,
                class_id=class_id,
                embedding_model_id="fake-embed-3",
            )
        ],
    )
    conn.execute("update jobs set state = 'done' where file_id = %s::uuid", (file_id,))
    return file_id, staged


def rows(db_other, file_id):
    return [
        db_other.execute(
            f"select count(*) from {t} where file_id = %s::uuid", (file_id,)
        ).fetchone()[0]
        for t in ("files", "jobs", "chunks")
    ]


def test_example_1_delete_removes_one_file_and_keeps_the_other(db, db_other, tmp_path):
    conn, owner, class_id = db
    conn.autocommit = True
    week1, path1 = ready_file(conn, owner, class_id, tmp_path, "week-1.pdf")
    week2, path2 = ready_file(conn, owner, class_id, tmp_path, "week-2.pdf")

    assert delete_file(conn, file_id=week1, owner_id=owner) is True
    assert rows(db_other, week1) == [0, 0, 0]
    assert not path1.exists()
    assert rows(db_other, week2) == [1, 1, 1]
    assert path2.exists()
    assert get_file_status(conn, file_id=week1, owner_id=owner) is None
    got = retrieve(conn, "q", owner, class_id, embedder=FakeEmbeddings(), k=10)
    assert {c.file for c in got} == {"week-2.pdf"}


def test_example_2_another_owner_cannot_delete(db, db_other, tmp_path):
    conn, owner, class_id = db
    conn.autocommit = True
    week2, path2 = ready_file(conn, owner, class_id, tmp_path, "week-2.pdf")
    assert delete_file(conn, file_id=week2, owner_id="someone-else") is False
    assert rows(db_other, week2) == [1, 1, 1]
    assert path2.exists()


@pytest.fixture
def http(db):
    _, owner, _ = db
    app = create_app(embedder=FakeEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_example_5_delete_route_then_status_is_404(http, db, tmp_path):
    conn, owner, class_id = db
    conn.autocommit = True
    week2, _ = ready_file(conn, owner, class_id, tmp_path, "week-2.pdf")
    response = http.delete(f"/files/{week2}")
    assert response.status_code == 204
    assert response.content == b""
    assert http.get(f"/files/{week2}").status_code == 404


def test_example_8_a_processing_file_is_409(http, db, db_other, tmp_path):
    conn, owner, class_id = db
    conn.autocommit = True
    staged = stage(io.BytesIO(b"bytes"), filename="busy.pdf", staging_dir=tmp_path)
    file_id = enqueue(conn, path=staged, owner_id=owner, class_id=class_id)
    conn.execute("update files set status = 'processing' where file_id = %s::uuid", (file_id,))
    response = http.delete(f"/files/{file_id}")
    assert response.status_code == 409
    assert response.json()["error"]["kind"] == "file_busy"
    assert rows(db_other, file_id) == [1, 1, 0]
