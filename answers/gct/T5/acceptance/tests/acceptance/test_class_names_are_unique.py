"""Acceptance tests for the ticket: worked examples 1, 2, 5 and 6."""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.classes import ClassNameTaken, create_class
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


def test_examples_1_and_2_same_name_or_different_case_is_refused(db, db_other):
    conn, owner, _ = db
    conn.autocommit = True
    create_class(conn, owner_id=owner, name="Biology 101")
    for name in ("Biology 101", "biology 101", "BIOLOGY 101"):
        with pytest.raises(ClassNameTaken):
            create_class(conn, owner_id=owner, name=name)
    count = db_other.execute(
        "select count(*) from classes where owner_id = %s and name = 'Biology 101'", (owner,)
    ).fetchone()[0]
    assert count == 1


def test_example_5_another_owner_may_use_the_name(db):
    conn, owner, _ = db
    conn.autocommit = True
    create_class(conn, owner_id=owner, name="Biology 101")
    other = f"{owner}-p"
    try:
        assert create_class(conn, owner_id=other, name="biology 101")
    finally:
        conn.execute("delete from classes where owner_id = %s", (other,))


def test_example_6_the_route_answers_409(db):
    _, owner, _ = db
    app = create_app(embedder=StubEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.post("/classes", json={"name": "Biology 101"}).status_code == 201
        response = client.post("/classes", json={"name": "biology 101"})
    assert response.status_code == 409
    assert response.json()["error"]["kind"] == "class_name_taken"
