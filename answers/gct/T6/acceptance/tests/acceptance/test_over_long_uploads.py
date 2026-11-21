"""Acceptance tests for the ticket: worked example 3, and the status message of worked example 1."""

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


class FakeEmbeddings:
    model_id = "fake-embed-3"
    dim = EMBEDDING_DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[1.0] + [0.0] * (EMBEDDING_DIM - 1) for _ in texts]


class StubGeneration:
    model_id = "stub-gen"

    def generate(self, messages) -> str:
        return ""


def deck(path, words_per_slide):
    prs = Presentation()
    for n in words_per_slide:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
        box.text_frame.text = " ".join(["w"] * n)
    prs.save(path)
    return path


@pytest.fixture
def http(worker_db):
    _, owner, _ = worker_db
    app = create_app(embedder=FakeEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def run_worker(conn):
    return process_one(
        conn,
        embedder=FakeEmbeddings(),
        chunk_size=CHUNK_SIZE_WORDS,
        chunk_overlap=CHUNK_OVERLAP_WORDS,
    )


def test_example_1_message_names_the_file_count_and_the_limit(worker_db, http, tmp_path):
    conn, owner, class_id = worker_db
    conn.autocommit = True
    source = deck(tmp_path / "book.pptx", [100_000, 100_000, 100_000, 12_400])
    file_id = enqueue(conn, path=str(source), owner_id=owner, class_id=class_id)
    assert run_worker(conn) is True
    message = http.get(f"/files/{file_id}").json()["message"]
    assert "312,400" in message
    assert "250,000" in message


def test_example_3_a_small_file_is_ready_as_usual(worker_db, http, tmp_path):
    conn, owner, class_id = worker_db
    conn.autocommit = True
    source = deck(tmp_path / "short.pptx", [100])
    file_id = enqueue(conn, path=str(source), owner_id=owner, class_id=class_id)
    assert run_worker(conn) is True
    body = http.get(f"/files/{file_id}").json()
    assert body["status"] == "ready"
    assert body["message"] == "This file is ready. You can ask questions about it now."
