"""Hidden tests for T7: `chunks.page_or_slide` becomes an integer without losing or guessing data.

Most tests build a scratch database at the schema the applied migrations produce, load rows into it,
and only then run `scripts/migrate.py` (twice, as CI does), the way a deploy meets real data.
"""

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
APPLIED = ["0001_init.sql", "0003_failed_reason_too_long.sql", "0004_one_worker.sql"]
VECTOR = "[" + ",".join(["0"] * (EMBEDDING_DIM - 1) + ["1"]) + "]"
OWNER = "t7-owner"


def _url_for(dbname: str) -> str:
    params = conninfo_to_dict(load_settings().database_url)
    params["dbname"] = dbname
    return make_conninfo(**params)


@pytest.fixture
def scratch(db):
    """A new database at the pre-change schema. Yields its conninfo; dropped afterwards."""
    conn, _, _ = db
    base = conninfo_to_dict(load_settings().database_url).get("dbname") or "postgres"
    name = f"{base}_t7_{uuid.uuid4().hex[:8]}"[:63]
    with psycopg.connect(load_settings().database_url, autocommit=True) as admin:
        admin.execute(f'create database "{name}"')
    url = _url_for(name)
    try:
        with psycopg.connect(url, autocommit=True) as c:
            c.execute("create extension if not exists vector")
            for fname in APPLIED:
                c.execute((ROOT / "migrations" / fname).read_text())
        yield url
    finally:
        with psycopg.connect(load_settings().database_url, autocommit=True) as admin:
            admin.execute(f'drop database if exists "{name}" with (force)')


def _seed(url: str, pages: list[str]) -> dict[str, str]:
    """One class, one file, one chunk per page value (stored as text). Returns chunk_id -> page."""
    with psycopg.connect(url, autocommit=True) as c:
        class_id = c.execute(
            "insert into classes (owner_id, name) values (%s, 'c') returning class_id::text",
            (OWNER,),
        ).fetchone()[0]
        file_id = c.execute(
            "insert into files (owner_id, class_id, filename, status) "
            "values (%s, %s::uuid, 'book.pdf', 'ready') returning file_id::text",
            (OWNER, class_id),
        ).fetchone()[0]
        out = {}
        for i, page in enumerate(pages):
            chunk_id = c.execute(
                "insert into chunks (file_id, owner_id, class_id, text, file, page_or_slide, "
                "embedding, embedding_model_id) values "
                "(%s::uuid, %s, %s::uuid, %s, 'book.pdf', %s::text, %s::vector, 'm') "
                "returning chunk_id::text",
                (file_id, OWNER, class_id, f"passage {i}", page, VECTOR),
            ).fetchone()[0]
            out[chunk_id] = page
        return out


def _migrate(url: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DATABASE_URL": url}
    return subprocess.run(
        [sys.executable, "scripts/migrate.py"], cwd=ROOT, env=env, capture_output=True, text=True
    )


def _column_type(url: str) -> str:
    with psycopg.connect(url) as c:
        return c.execute(
            "select data_type from information_schema.columns "
            "where table_schema = current_schema() and table_name = 'chunks' "
            "and column_name = 'page_or_slide'"
        ).fetchone()[0]


def _pages(url: str) -> dict[str, object]:
    with psycopg.connect(url) as c:
        rows = c.execute("select chunk_id::text, page_or_slide from chunks").fetchall()
    return dict(rows)


def test_existing_rows_survive_the_conversion_and_sort_as_numbers(scratch):
    seeded = _seed(scratch, ["1", "2", "10", "3", "10"])
    for _ in range(2):
        out = _migrate(scratch)
        assert out.returncode == 0, out.stderr
    assert _column_type(scratch) == "integer"
    assert _pages(scratch) == {cid: int(p) for cid, p in seeded.items()}
    with psycopg.connect(scratch) as c:
        ordered = [r[0] for r in c.execute("select page_or_slide from chunks order by 1")]
        texts = sorted(r[0] for r in c.execute("select text from chunks"))
    assert ordered == [1, 2, 3, 10, 10]
    assert texts == [f"passage {i}" for i in range(5)]


def test_a_fresh_database_migrates_to_an_integer_column_twice(scratch):
    """Same scratch schema, but no rows: the conversion must also be a clean no-op on re-run."""
    for _ in range(3):
        out = _migrate(scratch)
        assert out.returncode == 0, out.stderr
    assert _column_type(scratch) == "integer"


def test_a_bad_existing_value_stops_the_migration_and_changes_nothing(scratch):
    seeded = _seed(scratch, ["1", "iv", "7"])
    out = _migrate(scratch)
    assert out.returncode != 0, "a page value that is not a whole number must stop the migration"
    assert _column_type(scratch) == "text"
    assert _pages(scratch) == seeded, "no row may be deleted, nulled or rewritten"

    bad = next(cid for cid, p in seeded.items() if p == "iv")
    with psycopg.connect(scratch, autocommit=True) as c:
        c.execute("update chunks set page_or_slide = '0' where chunk_id = %s::uuid", (bad,))
    out = _migrate(scratch)
    assert out.returncode != 0, "a page number below 1 must stop the migration too"
    assert _column_type(scratch) == "text"
    assert _pages(scratch)[bad] == "0"

    with psycopg.connect(scratch, autocommit=True) as c:
        c.execute("update chunks set page_or_slide = '4' where chunk_id = %s::uuid", (bad,))
    out = _migrate(scratch)
    assert out.returncode == 0, out.stderr
    fixed = {**seeded, bad: "4"}
    assert _pages(scratch) == {cid: int(p) for cid, p in fixed.items()}


def test_the_database_refuses_a_page_below_one(db):
    conn, owner_id, class_id = db
    conn.autocommit = True
    file_id = str(uuid.uuid4())
    conn.execute(
        "insert into files (file_id, owner_id, class_id, filename, status) "
        "values (%s::uuid, %s, %s::uuid, 'x.pdf', 'ready')",
        (file_id, owner_id, class_id),
    )
    insert = (
        "insert into chunks (file_id, owner_id, class_id, text, file, page_or_slide, "
        "embedding, embedding_model_id) values (%s::uuid, %s, %s::uuid, 't', 'x.pdf', %s, "
        "%s::vector, 'm')"
    )
    conn.execute(insert, (file_id, owner_id, class_id, 1, VECTOR))
    for page in (0, -3):
        with pytest.raises(psycopg.errors.IntegrityError):
            conn.execute(insert, (file_id, owner_id, class_id, page, VECTOR))


class FakeEmbeddings:
    model_id = "fake-embed-3"

    def embed(self, texts):
        return [[0.0] * (EMBEDDING_DIM - 1) + [1.0] for _ in texts]


def test_index_file_stores_integers_and_retrieve_returns_them(db, db_other):
    conn, owner_id, class_id = db
    conn.autocommit = True
    file_id = str(uuid.uuid4())
    chunks = [
        PreparedChunk(
            text=f"page {p}",
            file="book.pdf",
            page_or_slide=p,
            embedding=[0.0] * (EMBEDDING_DIM - 1) + [1.0],
            owner_id=owner_id,
            class_id=class_id,
            embedding_model_id="fake-embed-3",
        )
        for p in (2, 10, 1)
    ]
    index_file(
        conn,
        file_id=file_id,
        filename="book.pdf",
        owner_id=owner_id,
        class_id=class_id,
        chunks=chunks,
    )
    rows = db_other.execute(
        "select pg_typeof(page_or_slide)::text, page_or_slide from chunks "
        "where file_id = %s::uuid order by page_or_slide",
        (file_id,),
    ).fetchall()
    assert rows == [("integer", 1), ("integer", 2), ("integer", 10)]
    got = retrieve(conn, "anything", owner_id, class_id, embedder=FakeEmbeddings(), k=10)
    assert sorted(c.page_or_slide for c in got) == [1, 2, 10]
    assert all(type(c.page_or_slide) is int for c in got)
