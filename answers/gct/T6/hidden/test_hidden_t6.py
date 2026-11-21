"""Hidden tests for T6: the amended request, after the conflict with ADR 0029 was raised.

A file over the word limit is still refused whole (`failed` / `too_long`, no chunks, nothing
embedded), which is what the request as first written would have broken; and its status message
now tells the student how many words the file has.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient
from pptx import Presentation
from pptx.util import Inches

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.config import EMBEDDING_DIM
from gct.ingest.chunk import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from gct.jobs.queue import enqueue
from gct.jobs.worker import process_one

LIMIT = 250_000


class CountingEmbeddings:
    model_id = "fake-embed-3"
    dim = EMBEDDING_DIM

    def __init__(self) -> None:
        self.calls: list[int] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(len(texts))
        return [[1.0] + [0.0] * (EMBEDDING_DIM - 1) for _ in texts]


class StubGeneration:
    model_id = "stub-gen"

    def generate(self, messages) -> str:
        return ""


def deck(path, words_per_slide: list[int]):
    prs = Presentation()
    for n in words_per_slide:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
        box.text_frame.text = " ".join(["w"] * n)
    prs.save(path)
    return path


def tick(conn, embedder) -> bool:
    return process_one(
        conn, embedder=embedder, chunk_size=CHUNK_SIZE_WORDS, chunk_overlap=CHUNK_OVERLAP_WORDS
    )


@pytest.fixture
def http(worker_db):
    _, owner, _ = worker_db
    app = create_app(embedder=CountingEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def _rows(db_other, file_id) -> tuple:
    return db_other.execute(
        """
        select f.status, f.failed_reason, j.state,
               (select count(*) from chunks c where c.file_id = f.file_id)
        from files f join jobs j using (file_id) where f.file_id = %s::uuid
        """,
        (file_id,),
    ).fetchone()


def test_an_over_limit_file_is_refused_whole_and_its_status_says_how_long_it_is(
    worker_db, db_other, http, tmp_path
):
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    source = deck(tmp_path / "textbook.pptx", [50_000] * 5 + [1])  # 250,001 words
    file_id = enqueue(conn, path=str(source), owner_id=owner_id, class_id=class_id)
    embedder = CountingEmbeddings()

    assert tick(conn, embedder) is True

    assert _rows(db_other, file_id) == ("failed", "too_long", "failed", 0)
    assert embedder.calls == [], "nothing may be embedded for a file that is refused"
    response = http.get(f"/files/{file_id}")
    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["failed_reason"]) == ("failed", "too_long")
    assert "250,001" in body["message"], "the message must give the file's own word count"
    assert f"{LIMIT:,}" in body["message"], "the message must still give the limit"


def test_the_count_is_the_files_own_and_small_files_are_unaffected(
    worker_db, db_other, http, tmp_path
):
    conn, owner_id, class_id = worker_db
    conn.autocommit = True
    big = deck(tmp_path / "big.pptx", [100_000, 100_000, 100_000, 12_400])  # 312,400 words
    big_id = enqueue(conn, path=str(big), owner_id=owner_id, class_id=class_id)
    small = deck(tmp_path / "small.pptx", [40, 60])
    small_id = enqueue(conn, path=str(small), owner_id=owner_id, class_id=class_id)
    embedder = CountingEmbeddings()

    assert tick(conn, embedder) is True
    assert tick(conn, embedder) is True

    assert _rows(db_other, big_id) == ("failed", "too_long", "failed", 0)
    message = http.get(f"/files/{big_id}").json()["message"]
    assert "312,400" in message
    assert "250,001" not in message

    status, reason, state, n_chunks = _rows(db_other, small_id)
    assert (status, reason, state) == ("ready", None, "done")
    assert n_chunks > 0
    small_body = http.get(f"/files/{small_id}").json()
    assert small_body["status"] == "ready"
    assert small_body["message"] == "This file is ready. You can ask questions about it now."
