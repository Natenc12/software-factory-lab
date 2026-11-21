"""Hidden tests for T8: each proves one planted bug in `GET /classes/{class_id}/files` exists.

All three fail on `base/T8` and pass once the bugs are fixed, and they do not depend on one
another: fixing one bug turns exactly its own test green.
"""

from __future__ import annotations

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
def http(db):
    _, owner, _ = db
    app = create_app(embedder=StubEmbeddings(), generator=StubGeneration())
    app.dependency_overrides[owner_dep] = lambda: owner
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def _upload(conn, owner_id, class_id, tmp_path, name) -> str:
    path = tmp_path / name
    path.write_bytes(b"%PDF-1.7 placeholder")
    return enqueue(conn, path=str(path), owner_id=owner_id, class_id=class_id)


def test_bug_1_page_one_is_the_first_page(http, db, tmp_path):
    """Planted bug 1 (visible in the diff): the offset is `page * per_page`, so page 1 skips
    the newest `per_page` files and the last page is never reachable."""
    conn, owner_id, class_id = db
    conn.autocommit = True
    ids = [_upload(conn, owner_id, class_id, tmp_path, f"f{i}.pdf") for i in range(3)]
    newest_first = list(reversed(ids))

    page1 = http.get(f"/classes/{class_id}/files", params={"page": 1, "per_page": 2})
    assert page1.status_code == 200
    assert [f["file_id"] for f in page1.json()["files"]] == newest_first[:2]

    page2 = http.get(f"/classes/{class_id}/files", params={"page": 2, "per_page": 2})
    assert page2.status_code == 200
    assert [f["file_id"] for f in page2.json()["files"]] == newest_first[2:]


def test_bug_2_an_empty_class_is_an_empty_list_not_a_404(http, db):
    """Planted bug 2 (missed edge case): `if not files` treats an empty class as a missing one."""
    _, _, class_id = db
    response = http.get(f"/classes/{class_id}/files")
    assert response.status_code == 200
    assert response.json()["files"] == []


def test_bug_3_the_status_filter_runs(db, tmp_path):
    """Planted bug 3 (only when run): the filter casts to a `file_status` type that does not
    exist, so any listing with a status filter fails inside Postgres (a 500 over HTTP). Checked
    through the library so the route's own bugs cannot mask it."""
    from gct.files import list_class_files

    conn, owner_id, class_id = db
    conn.autocommit = True
    _upload(conn, owner_id, class_id, tmp_path, "fine.pdf")
    broken = _upload(conn, owner_id, class_id, tmp_path, "broken.pdf")
    conn.execute(
        "update files set status = 'failed', failed_reason = 'unparseable' "
        "where file_id = %s::uuid",
        (broken,),
    )

    files = list_class_files(conn, class_id=class_id, owner_id=owner_id, status="failed")
    assert [f.file_id for f in files] == [broken]
    assert files[0].failed_reason == "unparseable"
    queued = list_class_files(conn, class_id=class_id, owner_id=owner_id, status="queued")
    assert [f.filename for f in queued] == ["fine.pdf"]
