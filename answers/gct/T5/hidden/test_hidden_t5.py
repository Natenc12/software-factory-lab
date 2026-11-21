"""Hidden tests for T5: one owner cannot create two classes with the same name.

They assume the owner's answer to the open question: names are the same when they match after
trimming, collapsing inner whitespace and ignoring letter case.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.classes import create_class
from gct.config import EMBEDDING_DIM, load_settings

ROOT = Path(__file__).resolve().parents[2]


class StubEmbeddings:
    model_id = "stub-embed"
    dim = EMBEDDING_DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[0.0] * self.dim for _ in texts]


class StubGeneration:
    model_id = "stub-gen"

    def generate(self, messages) -> str:
        return ""


def _names(db_other, owner_id: str) -> list[str]:
    rows = db_other.execute(
        "select name from classes where owner_id = %s order by created_at, name", (owner_id,)
    ).fetchall()
    return [r[0] for r in rows]


SAME = [
    "Biology 101",
    "biology 101",
    "BIOLOGY 101",
    "  Biology 101",
    "Biology  101 ",
    "Biology\t101",
]
DIFFERENT = ["Biology 102", "Biology-101", "Biologie 101", "Biology 1010"]


def test_a_name_that_differs_only_in_case_or_spacing_is_refused(db, db_other):
    from gct.classes import ClassNameTaken

    conn, owner_id, _ = db
    conn.autocommit = True
    create_class(conn, owner_id=owner_id, name="Biology 101")
    for variant in SAME:
        with pytest.raises(ClassNameTaken):
            create_class(conn, owner_id=owner_id, name=variant)
    assert _names(db_other, owner_id).count("Biology 101") == 1
    assert len(_names(db_other, owner_id)) == 2  # the fixture's class plus "Biology 101"


def test_names_that_really_differ_are_created_verbatim_and_owners_do_not_collide(db, db_other):
    from gct.classes import ClassNameTaken

    conn, owner_id, _ = db
    conn.autocommit = True
    create_class(conn, owner_id=owner_id, name="Biology 101")
    for name in DIFFERENT:
        create_class(conn, owner_id=owner_id, name=name)
    padded = "  Chemistry   One "
    create_class(conn, owner_id=owner_id, name=padded)
    assert padded in _names(db_other, owner_id), "the stored name is exactly what was typed"
    with pytest.raises(ClassNameTaken):
        create_class(conn, owner_id=owner_id, name="chemistry one")

    other = f"{owner_id}-someone-else"
    try:
        create_class(conn, owner_id=other, name="biology 101")
        assert _names(db_other, other) == ["biology 101"]
    finally:
        conn.execute("delete from classes where owner_id = %s", (other,))


@pytest.fixture
def http(db):
    _, owner, _ = db
    app = create_app(embedder=StubEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, app


def test_the_route_answers_409_class_name_taken(http, db, db_other):
    client, app = http
    _, owner_id, _ = db
    first = client.post("/classes", json={"name": "Philosophy of Religion"})
    assert first.status_code == 201
    assert first.json()["name"] == "Philosophy of Religion"

    again = client.post("/classes", json={"name": "philosophy  of religion"})
    assert again.status_code == 409
    error = again.json()["error"]
    assert error["kind"] == "class_name_taken"
    assert error["message"]
    assert _names(db_other, owner_id).count("Philosophy of Religion") == 1

    blank = client.post("/classes", json={"name": "   "})
    assert blank.status_code == 400
    assert blank.json()["error"]["kind"] == "blank_name"

    other = f"{owner_id}-other"
    app.dependency_overrides[owner_dep] = lambda: other
    try:
        theirs = client.post("/classes", json={"name": "Philosophy of Religion"})
        assert theirs.status_code == 201
    finally:
        db_other.execute("delete from classes where owner_id = %s", (other,))


def test_existing_duplicates_survive_a_deploy_and_still_block_new_ones(db, db_other):
    from gct.classes import ClassNameTaken

    conn, owner_id, _ = db
    conn.autocommit = True
    conn.execute(
        "insert into classes (owner_id, name) values (%s, 'Algebra'), (%s, 'algebra ')",
        (owner_id, owner_id),
    )
    env = {**os.environ, "DATABASE_URL": load_settings().database_url}
    out = subprocess.run(
        [sys.executable, "scripts/migrate.py"], cwd=ROOT, env=env, capture_output=True, text=True
    )
    assert out.returncode == 0, out.stderr
    names = _names(db_other, owner_id)
    assert "Algebra" in names and "algebra " in names, "existing classes must be left as they are"
    with pytest.raises(ClassNameTaken):
        create_class(conn, owner_id=owner_id, name="ALGEBRA")
