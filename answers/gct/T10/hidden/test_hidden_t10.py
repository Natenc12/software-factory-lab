"""Hidden tests for T10: the API calls a class a course, and every old name keeps working.

Each test checks new behaviour together with the old replies it must not disturb, word for word as
they are on the starting branch.
"""

from __future__ import annotations

import io
import json
import uuid
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gct.api.app import create_app
from gct.api.deps import owner_id as owner_dep
from gct.config import EMBEDDING_DIM, STAGING_DIR

ROOT = Path(__file__).resolve().parents[2]
PDF = b"%PDF-1.7 placeholder bytes"

OLD_BAD_CLASS = {
    "error": {
        "kind": "bad_class_id",
        "message": "class_id must be a uuid. Use the id returned when the class was created.",
        "detail": None,
    }
}
OLD_UPLOAD_NOT_FOUND = {
    "error": {
        "kind": "class_not_found",
        "message": "No such class. Check the class id, or create the class before uploading to it.",
        "detail": None,
    }
}
OLD_ASK_NOT_FOUND = {
    "error": {
        "kind": "class_not_found",
        "message": "No such class. Check the class id, or create the class before asking about it.",
        "detail": None,
    }
}


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


def staged() -> set[Path]:
    root = Path(STAGING_DIR)
    return {p for p in root.rglob("*") if p.is_file()} if root.exists() else set()


def upload(client, **form):
    return client.post("/files", data=form, files={"file": ("lecture.pdf", io.BytesIO(PDF))})


def test_post_courses_creates_a_course_that_old_routes_accept_as_a_class(client):
    r = client.post("/courses", json={"name": "Biology 101"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert set(body) == {"course_id", "name"}
    assert body["name"] == "Biology 101"
    course_id = body["course_id"]
    assert upload(client, class_id=course_id).status_code == 202

    blank = client.post("/courses", json={"name": "   "})
    assert blank.status_code == 400
    assert blank.json()["error"]["kind"] == "blank_name"

    old = client.post("/classes", json={"name": "Chemistry"})
    assert old.status_code == 201
    assert set(old.json()) == {"class_id", "name"}


def test_uploads_by_course_id_answer_in_course_words_and_old_replies_are_unchanged(client, db):
    _, _, class_id = db
    assert upload(client, course_id=class_id).status_code == 202

    unknown = upload(client, course_id=str(uuid.uuid4()))
    assert unknown.status_code == 404
    assert unknown.json()["error"]["kind"] == "course_not_found"
    assert "course" in unknown.json()["error"]["message"]
    bad = upload(client, course_id="biology")
    assert bad.status_code == 400
    assert bad.json()["error"]["kind"] == "bad_course_id"
    assert "course" in bad.json()["error"]["message"]

    # Old clients: exactly what they got before.
    assert upload(client, class_id=class_id).status_code == 202
    assert upload(client, class_id=str(uuid.uuid4())).json() == OLD_UPLOAD_NOT_FOUND
    assert upload(client, class_id="biology").json() == OLD_BAD_CLASS
    missing = upload(client)
    assert missing.status_code == 422
    assert missing.json()["error"]["kind"] == "validation"
    assert any("class_id" in str(entry) for entry in missing.json()["error"]["detail"])


def test_conflicting_ids_are_refused_before_anything_is_staged(client, db):
    _, _, class_id = db
    other = str(uuid.uuid4())
    before = staged()
    for form in (
        {"class_id": class_id, "course_id": other},
        {"class_id": class_id, "course_id": "biology"},
    ):
        r = upload(client, **form)
        assert r.status_code == 400, form
        assert r.json()["error"]["kind"] == "conflicting_ids"
    assert staged() == before, "a refused upload must not stage anything"

    same = upload(client, class_id=class_id, course_id=uuid.UUID(class_id).urn)
    assert same.status_code == 202

    ask = client.post(
        "/ask", json={"class_id": class_id, "course_id": other, "question": "what is it?"}
    )
    assert ask.status_code == 400
    assert ask.json()["error"]["kind"] == "conflicting_ids"


def test_ask_by_course_id_answers_in_course_words_and_old_replies_are_unchanged(client, db):
    _, _, class_id = db
    ok = client.post("/ask", json={"course_id": class_id, "question": "what is it?"})
    assert ok.status_code == 200, ok.text
    both = client.post(
        "/ask", json={"course_id": class_id, "class_id": class_id, "question": "what is it?"}
    )
    assert both.status_code == 200

    unknown = client.post("/ask", json={"course_id": str(uuid.uuid4()), "question": "q?"})
    assert unknown.status_code == 404
    assert unknown.json()["error"]["kind"] == "course_not_found"
    assert "course" in unknown.json()["error"]["message"]
    bad = client.post("/ask", json={"course_id": "biology", "question": "q?"})
    assert bad.status_code == 400
    assert bad.json()["error"]["kind"] == "bad_course_id"

    assert client.post("/ask", json={"class_id": class_id, "question": "q?"}).status_code == 200
    old_unknown = client.post("/ask", json={"class_id": str(uuid.uuid4()), "question": "q?"})
    assert old_unknown.json() == OLD_ASK_NOT_FOUND
    old_bad = client.post("/ask", json={"class_id": "biology", "question": "q?"})
    assert old_bad.json() == OLD_BAD_CLASS
    neither = client.post("/ask", json={"question": "q?"})
    assert neither.status_code == 422
    assert neither.json()["error"]["kind"] == "validation"


def test_the_old_route_is_marked_deprecated_in_the_live_and_the_committed_schema(client):
    live = client.get("/openapi.json").json()
    assert live["paths"]["/classes"]["post"].get("deprecated") is True
    assert not live["paths"]["/courses"]["post"].get("deprecated", False)
    committed = json.loads((ROOT / "web" / "openapi.json").read_text(encoding="utf-8"))
    assert committed["paths"]["/classes"]["post"].get("deprecated") is True
    assert "/courses" in committed["paths"]


# --- the Deprecation header ------------------------------------------------------------------


def flagged(response) -> bool:
    return response.headers.get("deprecation") == "true"


def test_every_reply_to_an_old_name_request_carries_the_deprecation_header(client, db):
    _, _, class_id = db
    unknown = str(uuid.uuid4())

    assert flagged(client.post("/classes", json={"name": "Physics"}))
    assert flagged(client.post("/classes", json={"name": "   "}))

    replies = [
        upload(client, class_id=class_id),
        upload(client, class_id=unknown),
        upload(client, class_id="biology"),
        client.post(
            "/files",
            data={"class_id": class_id},
            files={"file": ("bad\\name.pdf", io.BytesIO(PDF))},
        ),
        client.post("/ask", json={"class_id": class_id, "question": "what is it?"}),
        client.post("/ask", json={"class_id": unknown, "question": "what is it?"}),
    ]
    assert [r.status_code for r in replies] == [202, 404, 400, 400, 200, 404]
    assert replies[3].json()["error"]["kind"] == "bad_filename"
    assert all(flagged(r) for r in replies), [r.headers.get("deprecation") for r in replies]


def test_requests_that_use_course_id_never_carry_the_deprecation_header(client, db):
    _, _, class_id = db
    other = str(uuid.uuid4())
    replies = [
        client.post("/courses", json={"name": "Geology"}),
        upload(client, course_id=class_id),
        upload(client, course_id=other),
        upload(client, course_id=class_id, class_id=class_id),
        upload(client, course_id=other, class_id=class_id),
        client.post("/ask", json={"course_id": class_id, "question": "what is it?"}),
        client.get(f"/courses/{class_id}"),
    ]
    assert [r.status_code for r in replies] == [201, 202, 404, 202, 400, 200, 200]
    assert not any("deprecation" in r.headers for r in replies)


# --- GET /courses/{course_id} ----------------------------------------------------------------


def test_a_course_summary_counts_its_files_by_status(client, db):
    conn, owner, _ = db
    conn.autocommit = True
    course_id = client.post("/courses", json={"name": "Art History"}).json()["course_id"]
    for _ in range(4):
        assert upload(client, course_id=course_id).status_code == 202
    ids = [
        r[0]
        for r in conn.execute(
            "select file_id::text from files where class_id = %s::uuid order by created_at",
            (course_id,),
        ).fetchall()
    ]
    conn.execute("update files set status = 'ready' where file_id = %s::uuid", (ids[0],))
    conn.execute(
        "update files set status = 'failed', failed_reason = 'empty' where file_id = %s::uuid",
        (ids[1],),
    )

    r = client.get(f"/courses/{course_id}")
    assert r.status_code == 200, r.text
    assert r.json() == {
        "course_id": course_id,
        "name": "Art History",
        "files": {"queued": 2, "processing": 0, "ready": 1, "failed": 1},
    }
    assert client.get(f"/courses/{uuid.UUID(course_id).urn}").json()["course_id"] == course_id

    unknown = client.get(f"/courses/{uuid.uuid4()}")
    assert unknown.status_code == 404
    assert unknown.json()["error"]["kind"] == "course_not_found"
    bad = client.get("/courses/biology")
    assert bad.status_code == 400
    assert bad.json()["error"]["kind"] == "bad_course_id"

    other_owner = f"{owner}-other"
    theirs = conn.execute(
        "insert into classes (owner_id, name) values (%s, 'theirs') returning class_id::text",
        (other_owner,),
    ).fetchone()[0]
    try:
        assert client.get(f"/courses/{theirs}").json() == unknown.json()
    finally:
        conn.execute("delete from classes where owner_id = %s", (other_owner,))
