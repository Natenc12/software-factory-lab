"""Acceptance tests for the ticket: worked examples 1, 2, 4, 5 and 6."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from gct.classes import class_exists
from gct.config import EMBEDDING_DIM
from gct.ingest.index import index_file
from gct.ingest.pipeline import PreparedChunk
from gct.retriever.retrieve import retrieve


class FakeEmbeddings:
    model_id = "fake-embed-3"

    def embed(self, texts):
        return [[1.0] + [0.0] * (EMBEDDING_DIM - 1) for _ in texts]


def chunk(owner_id, class_id, text, page=1):
    return PreparedChunk(
        text=text,
        file="lecture.pdf",
        page_or_slide=page,
        embedding=[1.0] + [0.0] * (EMBEDDING_DIM - 1),
        owner_id=owner_id,
        class_id=class_id,
        embedding_model_id="fake-embed-3",
    )


def seed(conn, owner_id, class_id):
    conn.autocommit = True
    index_file(
        conn,
        file_id=str(uuid.uuid4()),
        filename="lecture.pdf",
        owner_id=owner_id,
        class_id=class_id,
        chunks=[chunk(owner_id, class_id, "alpha chunk"), chunk(owner_id, class_id, "beta", 2)],
    )
    conn.autocommit = False


def test_example_1_class_exists_accepts_every_spelling(db):
    conn, owner_id, class_id = db
    u = uuid.UUID(class_id)
    for spelled in (u.urn, str(u).upper(), f"{{{u}}}", u.hex):
        assert class_exists(conn, class_id=spelled, owner_id=owner_id) is True, spelled


def test_example_2_class_exists_refuses_non_ids_with_value_error(db):
    conn, owner_id, class_id = db
    for bad in (None, 12345, uuid.UUID(class_id), "intro-to-religion"):
        with pytest.raises(ValueError, match="class_id"):
            class_exists(conn, class_id=bad, owner_id=owner_id)


def test_example_4_retrieve_reaches_the_same_chunks_with_a_urn_spelling(db):
    conn, owner_id, class_id = db
    seed(conn, owner_id, class_id)
    e = FakeEmbeddings()
    baseline = retrieve(conn, "what is it?", owner_id, class_id, embedder=e)
    assert baseline
    assert retrieve(conn, "what is it?", owner_id, uuid.UUID(class_id).urn, embedder=e) == baseline


def test_example_5_a_refused_retrieve_leaves_the_connection_usable(db):
    conn, owner_id, class_id = db
    seed(conn, owner_id, class_id)
    e = FakeEmbeddings()
    conn.execute("select 1").fetchone()
    assert conn.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS
    with pytest.raises(ValueError, match="class_id"):
        retrieve(conn, "what is it?", owner_id, "intro-to-religion", embedder=e)
    assert conn.execute("select 1").fetchone() == (1,)
    assert retrieve(conn, "what is it?", owner_id, class_id, embedder=e)
    conn.rollback()


def test_example_6_index_file_stores_the_canonical_class_id(db, db_other):
    conn, owner_id, class_id = db
    conn.autocommit = True
    urn = uuid.UUID(class_id).urn
    file_id = str(uuid.uuid4())
    index_file(
        conn,
        file_id=file_id,
        filename="lecture.pdf",
        owner_id=owner_id,
        class_id=urn,
        chunks=[chunk(owner_id, urn, "one"), chunk(owner_id, urn, "two", 2)],
    )
    assert db_other.execute(
        "select class_id::text from files where file_id = %s::uuid", (file_id,)
    ).fetchone() == (class_id,)
    assert db_other.execute(
        "select distinct class_id::text from chunks where file_id = %s::uuid", (file_id,)
    ).fetchall() == [(class_id,)]
