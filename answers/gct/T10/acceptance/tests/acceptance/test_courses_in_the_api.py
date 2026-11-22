"""Acceptance tests for the ticket: worked examples 1, 2, 3, 5, 6 and 8."""

from __future__ import annotations

import io
import uuid
from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.config import EMBEDDING_DIM


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


def upload(client, **form):
    return client.post("/files", data=form, files={"file": ("a.pdf", io.BytesIO(b"%PDF-1.7 x"))})


def test_example_1_post_courses(client):
    r = client.post("/courses", json={"name": "Biology 101"})
    assert r.status_code == 201
    assert r.json()["name"] == "Biology 101"
    assert set(r.json()) == {"course_id", "name"}


def test_examples_2_3_upload_by_course_id(client, db):
    _, _, class_id = db
    assert upload(client, course_id=class_id).status_code == 202
    r = upload(client, course_id=str(uuid.uuid4()))
    assert r.status_code == 404
    assert r.json()["error"]["kind"] == "course_not_found"


def test_example_5_old_upload_reply_is_unchanged(client):
    r = upload(client, class_id=str(uuid.uuid4()))
    assert r.json() == {
        "error": {
            "kind": "class_not_found",
            "message": "No such class. Check the class id, or create the class before "
            "uploading to it.",
            "detail": None,
        }
    }


def test_example_6_conflicting_ids(client, db):
    _, _, class_id = db
    r = upload(client, class_id=class_id, course_id=str(uuid.uuid4()))
    assert r.status_code == 400
    assert r.json()["error"]["kind"] == "conflicting_ids"


def test_example_8_ask_by_course_id(client, db):
    _, _, class_id = db
    r = client.post("/ask", json={"course_id": class_id, "question": "what is it?"})
    assert r.status_code == 200
