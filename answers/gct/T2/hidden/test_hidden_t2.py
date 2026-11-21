"""Hidden tests for T2: an error reply never fails on, or mirrors, what the client sent.

Adapted from the tests that came with the real fix. They drive the real app from `create_app`, with
stub providers, so they hold however the fix is wired in.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

from gct.api.app import create_app
from gct.config import EMBEDDING_DIM

BOUND = 512
ENTRY_KEYS = {"type", "loc", "msg", "input"}


class StubEmbeddings:
    model_id = "stub-embed"
    dim = EMBEDDING_DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.0] * self.dim for _ in texts]


class StubGeneration:
    model_id = "stub-gen"

    def generate(self, messages) -> str:
        return ""


class ProbeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    count: int = 0


def _client() -> TestClient:
    app = create_app(embedder=StubEmbeddings(), generator=StubGeneration())

    @app.post("/probe")
    def _probe(body: ProbeBody) -> dict:
        return {"ok": True}

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def probe():
    with _client() as client:
        yield client


@pytest.fixture
def classes(db):
    with TestClient(
        create_app(embedder=StubEmbeddings(), generator=StubGeneration()),
        raise_server_exceptions=False,
    ) as client:
        yield client


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


@pytest.mark.parametrize(
    "content_type",
    [None, "application/octet-stream", "multipart/form-data", "text/plain"],
)
def test_one_undecodable_byte_is_a_422_with_its_field_list(probe, content_type):
    headers = {} if content_type is None else {"content-type": content_type}
    response = probe.post("/probe", content=b"\xff", headers=headers)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["kind"] == "validation"
    entry = error["detail"][0]
    assert set(entry) >= ENTRY_KEYS
    assert entry["loc"] == ["body"]
    assert entry["msg"]
    assert entry["input"] == "�"


def test_a_multi_megabyte_body_is_refused_without_being_echoed_back(probe):
    body = b"x" * 2_000_000
    response = probe.post("/probe", content=body, headers={"content-type": "multipart/form-data"})

    assert response.status_code == 422
    assert len(response.content) < 4096
    entry = response.json()["error"]["detail"][0]
    assert set(entry) >= ENTRY_KEYS
    assert entry["loc"] == ["body"]
    assert entry["input"].startswith("xxxx")
    assert len(entry["input"]) <= BOUND
    assert str(len(body)) in entry["input"]

    # An ordinary rejected value still comes back whole, in the same shape.
    response = probe.post("/probe", json={"nope": 1, "why": "because"})
    assert response.status_code == 422
    entries = response.json()["error"]["detail"]
    assert all(set(e) >= ENTRY_KEYS for e in entries)
    assert {"nope": 1, "why": "because"} in [e["input"] for e in entries]


def test_a_long_string_inside_a_json_body_is_bounded_and_the_boundary_is_exact(probe):
    exact = "y" * BOUND
    response = probe.post("/probe", json={"name": "ok", "count": exact})
    assert response.status_code == 422
    (entry,) = response.json()["error"]["detail"]
    assert entry["loc"] == ["body", "count"]
    assert entry["input"] == exact, "a string at the bound comes back exactly as sent"

    over = "y" * (BOUND + 1)
    response = probe.post("/probe", json={"name": "ok", "count": over})
    assert response.status_code == 422
    (entry,) = response.json()["error"]["detail"]
    assert entry["input"] != over
    assert len(entry["input"]) <= BOUND
    assert entry["input"].startswith("yyyy")
    assert str(BOUND + 1) in entry["input"]

    big = "z" * 60_000
    response = probe.post("/probe", json={"name": "ok", "count": big})
    assert response.status_code == 422
    assert len(response.content) < 4096
    assert all(len(s) <= BOUND for s in _strings(response.json()))

    # Strings nested inside a rejected object are bounded too: a missing required field echoes the
    # whole body object as `input`.
    for body in ({"nome": big}, {"k" * 5_000: 1}):
        response = probe.post("/probe", json=body)
        assert response.status_code == 422
        assert len(response.content) < 4096
        assert all(len(s) <= BOUND for s in _strings(response.json()))


def test_a_client_sized_key_is_bounded_where_it_is_echoed(probe):
    key = "k" * 5_000
    response = probe.post("/probe", json={"name": "ok", key: 1})

    assert response.status_code == 422
    entries = response.json()["error"]["detail"]
    locs = [entry["loc"] for entry in entries if entry["loc"][:1] == ["body"]]
    assert locs, entries
    assert all(len(part) <= BOUND for loc in locs for part in loc if isinstance(part, str))
    assert all(len(s) <= BOUND for s in _strings(response.json()))
    assert len(response.content) < 4096


def test_classes_route_undecodable_body_is_a_422(classes):
    response = classes.post("/classes", content=b"\xff")

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["kind"] == "validation"
    assert error["detail"][0]["loc"] == ["body"]


def test_classes_route_multi_megabyte_multipart_body_is_not_echoed_back(classes):
    body = b"x" * 2_000_000
    response = classes.post(
        "/classes", content=body, headers={"content-type": "multipart/form-data"}
    )
    assert response.status_code == 422
    assert len(response.content) < 4096
    assert response.json()["error"]["detail"][0]["loc"] == ["body"]

    response = classes.post("/classes", json={"nome": "Philosophy 101"})
    assert response.status_code == 422
    entry = response.json()["error"]["detail"][0]
    assert entry["loc"] == ["body", "name"]
    assert entry["input"] == {"nome": "Philosophy 101"}
