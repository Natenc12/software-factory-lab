"""Acceptance tests for the ticket: worked examples 1, 3 and 4, on `POST /classes`."""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient

from gct.api.app import create_app
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
    app = create_app(embedder=StubEmbeddings(), generator=StubGeneration())
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_example_1_one_undecodable_byte_is_a_422(client):
    response = client.post("/classes", content=b"\xff")
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["kind"] == "validation"
    assert error["detail"][0]["loc"] == ["body"]
    assert error["detail"][0]["input"] == "�"


def test_example_3_a_two_megabyte_multipart_body_is_not_echoed_back(client):
    body = b"x" * 2_000_000
    response = client.post(
        "/classes", content=body, headers={"content-type": "multipart/form-data"}
    )
    assert response.status_code == 422
    assert len(response.content) < 4096
    entry = response.json()["error"]["detail"][0]
    assert entry["loc"] == ["body"]
    assert entry["input"].startswith("xxxx")
    assert "2000000" in entry["input"]


def test_example_4_an_ordinary_rejected_value_is_echoed_whole(client):
    response = client.post("/classes", json={"nome": "Philosophy 101"})
    assert response.status_code == 422
    entry = response.json()["error"]["detail"][0]
    assert entry["loc"] == ["body", "name"]
    assert entry["input"] == {"nome": "Philosophy 101"}
