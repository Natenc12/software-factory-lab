"""Acceptance tests for the ticket: worked examples 1, 4 and 5."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from gct.config import EMBEDDING_DIM, load_settings
from gct.ingest.index import index_file
from gct.ingest.pipeline import PreparedChunk
from gct.retriever.retrieve import retrieve

ROOT = Path(__file__).resolve().parents[2]
VECTOR = "[" + ",".join(["0"] * (EMBEDDING_DIM - 1) + ["1"]) + "]"


@pytest.fixture
def old_schema_db(db):
    """A new database built from the three applied migrations only."""
    base = conninfo_to_dict(load_settings().database_url).get("dbname") or "postgres"
    name = f"{base}_acc_{uuid.uuid4().hex[:8]}"[:63]
    with psycopg.connect(load_settings().database_url, autocommit=True) as admin:
        admin.execute(f'create database "{name}"')
    params = conninfo_to_dict(load_settings().database_url)
    params["dbname"] = name
    url = make_conninfo(**params)
    try:
        with psycopg.connect(url, autocommit=True) as c:
            c.execute("create extension if not exists vector")
            for f in ("0001_init.sql", "0003_failed_reason_too_long.sql", "0004_one_worker.sql"):
                c.execute((ROOT / "migrations" / f).read_text())
        yield url
    finally:
        with psycopg.connect(load_settings().database_url, autocommit=True) as admin:
            admin.execute(f'drop database if exists "{name}" with (force)')


def test_example_1_existing_pages_become_integers(old_schema_db):
    with psycopg.connect(old_schema_db, autocommit=True) as c:
        class_id = c.execute(
            "insert into classes (owner_id, name) values ('o', 'c') returning class_id"
        ).fetchone()[0]
        file_id = c.execute(
            "insert into files (owner_id, class_id, filename, status) "
            "values ('o', %s, 'b.pdf', 'ready') returning file_id",
            (class_id,),
        ).fetchone()[0]
        for page in ("1", "2", "10", "3"):
            c.execute(
                "insert into chunks (file_id, owner_id, class_id, text, file, page_or_slide, "
                "embedding, embedding_model_id) values (%s, 'o', %s, %s, 'b.pdf', %s::text, "
                "%s::vector, 'm')",
                (file_id, class_id, f"text {page}", page, VECTOR),
            )
    env = {**os.environ, "DATABASE_URL": old_schema_db}
    out = subprocess.run(
        [sys.executable, "scripts/migrate.py"], cwd=ROOT, env=env, capture_output=True, text=True
    )
    assert out.returncode == 0, out.stderr
    with psycopg.connect(old_schema_db) as c:
        rows = c.execute("select text, page_or_slide from chunks order by page_or_slide").fetchall()
    assert rows == [("text 1", 1), ("text 2", 2), ("text 3", 3), ("text 10", 10)]


class FakeEmbeddings:
    model_id = "fake-embed-3"

    def embed(self, texts):
        return [[0.0] * (EMBEDDING_DIM - 1) + [1.0] for _ in texts]


def test_example_4_index_and_retrieve_use_integers(db, db_other):
    conn, owner_id, class_id = db
    conn.autocommit = True
    file_id = str(uuid.uuid4())
    index_file(
        conn,
        file_id=file_id,
        filename="b.pdf",
        owner_id=owner_id,
        class_id=class_id,
        chunks=[
            PreparedChunk(
                text=f"p{p}",
                file="b.pdf",
                page_or_slide=p,
                embedding=[0.0] * (EMBEDDING_DIM - 1) + [1.0],
                owner_id=owner_id,
                class_id=class_id,
                embedding_model_id="fake-embed-3",
            )
            for p in (2, 10, 1)
        ],
    )
    pages = db_other.execute(
        "select page_or_slide from chunks where file_id = %s::uuid order by page_or_slide",
        (file_id,),
    ).fetchall()
    assert pages == [(1,), (2,), (10,)]
    got = retrieve(conn, "q", owner_id, class_id, embedder=FakeEmbeddings(), k=10)
    assert sorted(c.page_or_slide for c in got) == [1, 2, 10]


def test_example_5_page_zero_is_refused(db):
    conn, owner_id, class_id = db
    conn.autocommit = True
    file_id = str(uuid.uuid4())
    conn.execute(
        "insert into files (file_id, owner_id, class_id, filename, status) "
        "values (%s::uuid, %s, %s::uuid, 'x.pdf', 'ready')",
        (file_id, owner_id, class_id),
    )
    with pytest.raises(psycopg.errors.IntegrityError):
        conn.execute(
            "insert into chunks (file_id, owner_id, class_id, text, file, page_or_slide, "
            "embedding, embedding_model_id) values (%s::uuid, %s, %s::uuid, 't', 'x.pdf', 0, "
            "%s::vector, 'm')",
            (file_id, owner_id, class_id, VECTOR),
        )
