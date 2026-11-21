"""Hidden tests for T3: every caller-supplied class or file id is canonicalised or refused.

Adapted from the tests that came with the real fix. Each test covers one entry point in both
directions: every spelling `uuid.UUID` accepts reaches the same rows, and anything that is not a
uuid string is refused with `ValueError` naming the parameter.
"""

from __future__ import annotations

import io
import uuid

import psycopg
import pytest
from reportlab.pdfgen import canvas

from gct.classes import class_exists
from gct.config import EMBEDDING_DIM
from gct.files import get_file_status
from gct.ingest.index import index_file
from gct.ingest.pipeline import PreparedChunk, ingest_file
from gct.retriever.retrieve import retrieve

MODEL_ID = "fake-embed-3"
NON_IDS = ["intro-to-religion", None, 12345, uuid.UUID("6f1e1b4a-0f0e-4a3e-9a7d-2f0a1b2c3d4e")]


class FakeEmbeddings:
    model_id = MODEL_ID

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts):
        texts = list(texts)
        self.calls.append(texts)
        return [[1.0] + [0.0] * (EMBEDDING_DIM - 1) for _ in texts]


def spellings(canonical: str) -> dict[str, str]:
    u = uuid.UUID(canonical)
    return {
        "plain": str(u),
        "upper": str(u).upper(),
        "braced": f"{{{u}}}",
        "hex32": u.hex,
        "urn": u.urn,
    }


def chunk(owner_id: str, class_id: str, text: str, page: int = 1) -> PreparedChunk:
    return PreparedChunk(
        text=text,
        file="lecture.pdf",
        page_or_slide=page,
        embedding=[1.0] + [0.0] * (EMBEDDING_DIM - 1),
        owner_id=owner_id,
        class_id=class_id,
        embedding_model_id=MODEL_ID,
    )


def write_pdf(path, page_texts):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(612, 792))
    for text in page_texts:
        c.drawString(72, 700, text)
        c.showPage()
    c.save()
    path.write_bytes(buf.getvalue())
    return path


def seed_file(conn, owner_id: str, class_id: str, texts: list[str]) -> str:
    file_id = str(uuid.uuid4())
    was = conn.autocommit
    conn.autocommit = True
    index_file(
        conn,
        file_id=file_id,
        filename="lecture.pdf",
        owner_id=owner_id,
        class_id=class_id,
        chunks=[chunk(owner_id, class_id, t, i + 1) for i, t in enumerate(texts)],
    )
    conn.autocommit = was
    return file_id


def test_class_exists_accepts_every_spelling_and_refuses_non_ids(db):
    conn, owner_id, class_id = db
    conn.autocommit = True
    for name, spelled in spellings(class_id).items():
        assert class_exists(conn, class_id=spelled, owner_id=owner_id) is True, name
    other = str(uuid.uuid4())
    assert class_exists(conn, class_id=uuid.UUID(other).urn, owner_id=owner_id) is False
    for bad in NON_IDS:
        with pytest.raises(ValueError, match="class_id"):
            class_exists(conn, class_id=bad, owner_id=owner_id)


def test_get_file_status_accepts_every_spelling_and_refuses_non_ids(db):
    conn, owner_id, class_id = db
    file_id = seed_file(conn, owner_id, class_id, ["a passage"])
    conn.autocommit = True
    baseline = get_file_status(conn, file_id=file_id, owner_id=owner_id)
    assert baseline is not None
    for name, spelled in spellings(file_id).items():
        assert get_file_status(conn, file_id=spelled, owner_id=owner_id) == baseline, name
    for bad in NON_IDS:
        with pytest.raises(ValueError, match="file_id"):
            get_file_status(conn, file_id=bad, owner_id=owner_id)


def test_retrieve_reaches_the_same_chunks_under_every_spelling(db):
    conn, owner_id, class_id = db
    seed_file(conn, owner_id, class_id, ["alpha chunk", "beta chunk"])
    embedder = FakeEmbeddings()
    baseline = retrieve(conn, "what is the argument?", owner_id, class_id, embedder=embedder)
    assert {c.text for c in baseline} == {"alpha chunk", "beta chunk"}
    for name, spelled in spellings(class_id).items():
        got = retrieve(conn, "what is the argument?", owner_id, spelled, embedder=embedder)
        assert got == baseline, name


def test_retrieve_refuses_a_non_id_and_leaves_the_connection_usable(db):
    conn, owner_id, class_id = db
    seed_file(conn, owner_id, class_id, ["alpha chunk", "beta chunk"])
    embedder = FakeEmbeddings()
    for bad in NON_IDS:
        conn.execute("select 1").fetchone()
        assert conn.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS
        with pytest.raises(ValueError, match="class_id"):
            retrieve(conn, "what is the argument?", owner_id, bad, embedder=embedder)
        assert conn.info.transaction_status != psycopg.pq.TransactionStatus.INERROR
        assert conn.execute("select 1").fetchone() == (1,)
        still = retrieve(conn, "what is the argument?", owner_id, class_id, embedder=embedder)
        assert {c.text for c in still} == {"alpha chunk", "beta chunk"}
    conn.rollback()


def test_index_file_canonicalises_class_id_on_the_file_and_on_every_chunk(db, db_other):
    conn, owner_id, class_id = db
    conn.autocommit = True
    for name, spelled in spellings(class_id).items():
        file_id = str(uuid.uuid4())
        index_file(
            conn,
            file_id=file_id,
            filename="lecture.pdf",
            owner_id=owner_id,
            class_id=spelled,
            chunks=[chunk(owner_id, spelled, "one"), chunk(owner_id, spelled, "two", 2)],
        )
        row = db_other.execute(
            "select class_id::text, status from files where file_id = %s::uuid", (file_id,)
        ).fetchone()
        assert row == (class_id, "ready"), name
        chunk_classes = db_other.execute(
            "select distinct class_id::text from chunks where file_id = %s::uuid", (file_id,)
        ).fetchall()
        assert chunk_classes == [(class_id,)], name


def test_index_file_refuses_a_non_canonical_file_id_or_a_bad_class_id_and_writes_nothing(
    db, db_other
):
    conn, owner_id, class_id = db
    conn.autocommit = True
    target = str(uuid.uuid4())
    wrong_spellings = [v for k, v in spellings(target).items() if k in ("braced", "hex32", "urn")]
    for bad in [*wrong_spellings, None, 12345, uuid.UUID(target)]:
        with pytest.raises(ValueError, match="file_id"):
            index_file(
                conn,
                file_id=bad,
                filename="lecture.pdf",
                owner_id=owner_id,
                class_id=class_id,
                chunks=[chunk(owner_id, class_id, "one")],
            )
    for bad in NON_IDS:
        with pytest.raises(ValueError, match="class_id"):
            index_file(
                conn,
                file_id=target,
                filename="lecture.pdf",
                owner_id=owner_id,
                class_id=bad,
                chunks=[chunk(owner_id, class_id, "one")],
            )
    assert db_other.execute(
        "select count(*) from files where file_id = %s::uuid", (target,)
    ).fetchone() == (0,)
    assert db_other.execute(
        "select count(*) from chunks where file_id = %s::uuid", (target,)
    ).fetchone() == (0,)

    # The standard hyphenated form is accepted in either letter case.
    index_file(
        conn,
        file_id=target.upper(),
        filename="lecture.pdf",
        owner_id=owner_id,
        class_id=class_id,
        chunks=[chunk(owner_id, class_id, "one")],
    )
    assert db_other.execute(
        "select status from files where file_id = %s::uuid", (target,)
    ).fetchone() == ("ready",)


def test_ingest_file_refuses_a_bad_class_id_before_paying_for_embeddings(db, db_other, tmp_path):
    conn, owner_id, class_id = db
    conn.autocommit = True
    source = write_pdf(tmp_path / "week-1.pdf", ["the first lecture", "the second page"])
    for bad in NON_IDS:
        embedder = FakeEmbeddings()
        with pytest.raises(ValueError, match="class_id"):
            ingest_file(source, owner_id, bad, embedder=embedder, conn=conn)
        assert embedder.calls == [], f"{bad!r}: the embedding run was bought before the refusal"

    embedder = FakeEmbeddings()
    file_id = ingest_file(source, owner_id, uuid.UUID(class_id).urn, embedder=embedder, conn=conn)
    assert db_other.execute(
        "select class_id::text, status from files where file_id = %s::uuid", (file_id,)
    ).fetchone() == (class_id, "ready")
    assert db_other.execute(
        "select distinct class_id::text from chunks where file_id = %s::uuid", (file_id,)
    ).fetchall() == [(class_id,)]
