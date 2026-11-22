"""Hidden tests for T12: the owner's amended request, after the conflict was raised.

The ticket asks for a 403 `file_forbidden` when a file exists under another owner. That would tell
any caller which ids exist in other accounts; the code and its tests keep a missing file and another
owner's file one indistinguishable 404. The owner's real need (replies.md, T12-conflict-raised): the
reply stays the same, and the server log says, for support, that the file exists under another
owner, naming the file id and never the other owner.
"""

from __future__ import annotations

import logging
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


@pytest.fixture
def foreign_file(db, tmp_path):
    """A file that belongs to another owner, in that owner's own class."""
    conn, _, _ = db
    conn.autocommit = True
    other_owner = f"other-owner-{uuid.uuid4()}"
    other_class = str(uuid.uuid4())
    conn.execute(
        "insert into classes (class_id, owner_id, name) values (%s::uuid, %s, 'theirs')",
        (other_class, other_owner),
    )
    path = tmp_path / "theirs.pdf"
    path.write_bytes(b"%PDF-1.7 placeholder")
    file_id = enqueue(conn, path=path, owner_id=other_owner, class_id=other_class)
    yield file_id, other_owner
    conn.execute("delete from jobs where owner_id = %s", (other_owner,))
    conn.execute("delete from files where owner_id = %s", (other_owner,))
    conn.execute("delete from classes where owner_id = %s", (other_owner,))


def messages(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]


def test_another_owners_file_gets_the_missing_file_reply_and_one_log_line(
    client, foreign_file, caplog
):
    file_id, other_owner = foreign_file
    with caplog.at_level(logging.WARNING):
        foreign = client.get(f"/files/{file_id}")
    missing = client.get(f"/files/{uuid.uuid4()}")

    assert foreign.status_code == 404
    assert foreign.json() == missing.json(), "the reply must not tell the two cases apart"
    assert foreign.json()["error"]["kind"] == "file_not_found"
    logged = messages(caplog)
    assert sum(file_id in m for m in logged) == 1, "exactly one warning naming the file id"
    assert not any(other_owner in m for m in logged), "the other owner must never be logged"

    # The same, whatever spelling of the id the caller used.
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        urn = client.get(f"/files/{uuid.UUID(file_id).urn}")
    assert urn.json() == missing.json()
    assert sum(file_id in m for m in messages(caplog)) == 1


def test_unknown_ids_and_own_files_log_nothing_new(client, db, foreign_file, tmp_path, caplog):
    conn, owner, class_id = db
    file_id, other_owner = foreign_file
    path = tmp_path / "mine.pdf"
    path.write_bytes(b"%PDF-1.7 placeholder")
    mine = enqueue(conn, path=path, owner_id=owner, class_id=class_id)
    unknown = str(uuid.uuid4())

    with caplog.at_level(logging.WARNING):
        assert client.get(f"/files/{unknown}").status_code == 404
        assert client.get(f"/files/{mine}").status_code == 200
        foreign = client.get(f"/files/{file_id}")
    logged = messages(caplog)
    assert not any(unknown in m for m in logged), "an id that exists nowhere logs nothing"
    assert not any(mine in m for m in logged), "an owner reading their own file logs nothing"
    assert foreign.status_code == 404
    assert sum(file_id in m for m in logged) == 1
