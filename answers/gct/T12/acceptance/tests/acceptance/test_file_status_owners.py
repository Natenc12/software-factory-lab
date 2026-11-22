"""Acceptance tests for the ticket: worked examples 1 and 3."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.config import EMBEDDING_DIM
from gct.jobs.queue import enqueue


class StubEmbeddings:
    model_id = "stub-embed"
    dim = EMBEDDING_DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.0] * self.dim for _ in texts]


class StubGeneration:
    model_id = "stub-gen"

    def generate(self, messages) -> str:
        return ""


@pytest.fixture
def client(db):
    _, owner, _ = db
    app = create_app(embedder=StubEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_example_1_own_file_is_200(client, db, tmp_path):
    conn, owner, class_id = db
    conn.autocommit = True
    path = tmp_path / "mine.pdf"
    path.write_bytes(b"%PDF-1.7 x")
    file_id = enqueue(conn, path=path, owner_id=owner, class_id=class_id)
    response = client.get(f"/files/{file_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


def test_example_3_unknown_id_is_todays_404(client):
    response = client.get(f"/files/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "kind": "file_not_found",
            "message": "No such file. Check the file id returned when the file was uploaded.",
            "detail": None,
        }
    }
