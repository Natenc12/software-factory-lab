"""Reviewer's own checks, written from the contract before reading the diff."""
from __future__ import annotations

import sqlite3
import pytest

from lab import ask, classes, questions
from lab.models import Answer


class Counting:
    def __init__(self, name="counting", prefix=""):
        self.name = name
        self.prefix = prefix
        self.calls = []

    def answer(self, question, material):
        self.calls.append((question, material))
        return f"{self.prefix}A[{question}|{material}]"


@pytest.fixture(autouse=True)
def _clean():
    ask.clear_answer_cache()
    yield
    ask.clear_answer_cache()


def q(conn, klass, student, text):
    return questions.ask_question(conn, klass.id, student.id, text)


# E1: Ada then Ben, provider once, same body, own rows
def test_e1_ada_then_ben(conn, biology):
    klass, ada, ben = biology
    p = Counting()
    qa = q(conn, klass, ada, "What is DNA?")
    qb = q(conn, klass, ben, "What is DNA?")
    a1 = ask.answer(conn, qa.id, p)
    a2 = ask.answer(conn, qb.id, p)
    assert len(p.calls) == 1
    assert a1.body == a2.body
    assert a2.question_id == qb.id
    assert ask.get_answer(conn, qa.id) is not None and ask.get_answer(conn, qb.id) is not None
    assert conn.execute("select count(*) from answers").fetchone()[0] == 2


# E2: same question twice in a row
def test_e2_twice(conn, biology):
    klass, ada, _ = biology
    p = Counting()
    qa = q(conn, klass, ada, "What is DNA?")
    ask.answer(conn, qa.id, p)
    ask.answer(conn, qa.id, p)
    assert len(p.calls) == 1
    assert conn.execute("select count(*) from answers where question_id=?", (qa.id,)).fetchone()[0] == 1


# E3: clear
def test_e3_clear(conn, biology):
    klass, ada, _ = biology
    p = Counting()
    qa = q(conn, klass, ada, "What is DNA?")
    ask.answer(conn, qa.id, p)
    ask.clear_answer_cache()
    ask.answer(conn, qa.id, p)
    assert len(p.calls) == 2


# Amendment: per class
def test_am_per_class(conn, biology):
    klass, ada, _ = biology
    chem = classes.create_class(conn, "Chem", "Atoms bond.")
    cara = classes.enrol_student(conn, chem.id, "Cara")
    p = Counting()
    b = ask.answer(conn, q(conn, klass, ada, "What is DNA?").id, p)
    c = ask.answer(conn, q(conn, chem, cara, "What is DNA?").id, p)
    assert len(p.calls) == 2
    assert b.body != c.body
    assert "Atoms bond." in c.body


# Amendment: set_material invalidates
def test_am_set_material(conn, biology):
    klass, ada, ben = biology
    p = Counting()
    ask.answer(conn, q(conn, klass, ada, "What is DNA?").id, p)
    classes.set_material(conn, klass.id, "New material.")
    a = ask.answer(conn, q(conn, klass, ben, "What is DNA?").id, p)
    assert len(p.calls) == 2
    assert "New material." in a.body


# Amendment: material changed then changed back -> must still be correct body
def test_am_material_roundtrip(conn, biology):
    klass, ada, _ = biology
    p = Counting()
    qa = q(conn, klass, ada, "What is DNA?")
    first = ask.answer(conn, qa.id, p).body
    classes.set_material(conn, klass.id, "Other.")
    assert "Other." in ask.answer(conn, qa.id, p).body
    classes.set_material(conn, klass.id, klass.material)
    assert ask.answer(conn, qa.id, p).body == first


# Amendment: material changed outside set_material (direct SQL) -> next answer from new material
def test_am_material_direct_sql(conn, biology):
    klass, ada, _ = biology
    p = Counting()
    qa = q(conn, klass, ada, "What is DNA?")
    ask.answer(conn, qa.id, p)
    conn.execute("update classes set material='Direct.' where id=?", (klass.id,))
    conn.commit()
    assert "Direct." in ask.answer(conn, qa.id, p).body


# Decision: no normalising
def test_no_normalising(conn, biology):
    klass, ada, ben = biology
    p = Counting()
    ask.answer(conn, q(conn, klass, ada, "What is DNA?").id, p)
    ask.answer(conn, q(conn, klass, ben, "what is dna?").id, p)
    ask.answer(conn, q(conn, klass, ben, "What is DNA").id, p)
    assert len(p.calls) == 3


# MNC1: same body as without cache, incl. a different provider passed
def test_mnc_same_body_different_provider(conn, biology):
    klass, ada, ben = biology
    p1 = Counting("one", "ONE:")
    p2 = Counting("two", "TWO:")
    ask.answer(conn, q(conn, klass, ada, "What is DNA?").id, p1)
    qb = q(conn, klass, ben, "What is DNA?")
    a = ask.answer(conn, qb.id, p2)
    # Without the cache, p2 would answer with its own body
    assert a.body.startswith("TWO:"), a.body


# MNC1 with default provider: same body vs uncached
def test_mnc_same_body_default(conn, biology):
    klass, ada, ben = biology
    from lab.providers import get_provider
    expected = get_provider().answer("What is DNA?", klass.material)
    a1 = ask.answer(conn, q(conn, klass, ada, "What is DNA?").id)
    a2 = ask.answer(conn, q(conn, klass, ben, "What is DNA?").id)
    assert a1.body == a2.body == expected


# MNC2: Answer returned, provider column, row replaced on hit
def test_mnc_answer_row_on_hit(conn, biology):
    klass, ada, _ = biology
    p = Counting()
    qa = q(conn, klass, ada, "What is DNA?")
    a1 = ask.answer(conn, qa.id, p)
    a2 = ask.answer(conn, qa.id, p)
    assert isinstance(a2, Answer)
    assert a2 == ask.get_answer(conn, qa.id)
    assert a2.provider == "counting"
    assert conn.execute("select count(*) from answers").fetchone()[0] == 1


# MNC3: hidden refused even when cached
def test_mnc_hidden_after_cache(conn, biology):
    klass, ada, ben = biology
    p = Counting()
    ask.answer(conn, q(conn, klass, ada, "What is DNA?").id, p)
    qb = q(conn, klass, ben, "What is DNA?")
    questions.hide_question(conn, qb.id)
    with pytest.raises(ValueError):
        ask.answer(conn, qb.id, p)
    assert ask.get_answer(conn, qb.id) is None


def test_mnc_hidden_does_not_populate(conn, biology):
    klass, ada, ben = biology
    p = Counting()
    qa = q(conn, klass, ada, "What is DNA?")
    questions.hide_question(conn, qa.id)
    with pytest.raises(ValueError):
        ask.answer(conn, qa.id, p)
    assert p.calls == []
    ask.answer(conn, q(conn, klass, ben, "What is DNA?").id, p)
    assert len(p.calls) == 1


def test_mnc_missing(conn, biology):
    with pytest.raises(LookupError):
        ask.answer(conn, 9999, Counting())


# Failure path: provider raises -> nothing cached, next call retries
def test_provider_error_not_cached(conn, biology):
    klass, ada, _ = biology
    class Boom:
        name = "boom"
        n = 0
        def answer(self, question, material):
            Boom.n += 1
            raise RuntimeError("down")
    qa = q(conn, klass, ada, "What is DNA?")
    with pytest.raises(RuntimeError):
        ask.answer(conn, qa.id, Boom())
    p = Counting()
    ask.answer(conn, qa.id, p)
    assert len(p.calls) == 1


# Second DB in same process: class ids collide, material differs
def test_two_databases_same_process(tmp_path, monkeypatch, conn, biology):
    import importlib.util
    from pathlib import Path
    from lab.db import connect
    klass, ada, _ = biology
    p = Counting()
    ask.answer(conn, q(conn, klass, ada, "What is DNA?").id, p)
    root = Path(ask.__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("migrate2", root / "scripts" / "migrate.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    monkeypatch.setenv("LAB_DB", str(tmp_path / "other.db"))
    m.migrate()
    conn2 = connect()
    k2 = classes.create_class(conn2, "Biology", "Totally different.")
    s2 = classes.enrol_student(conn2, k2.id, "Zed")
    assert k2.id == klass.id
    a = ask.answer(conn2, questions.ask_question(conn2, k2.id, s2.id, "What is DNA?").id, p)
    conn2.close()
    assert "Totally different." in a.body, a.body


# Queue path still uses answer() and benefits
def test_queue_path(conn, biology):
    klass, ada, ben = biology
    p = Counting()
    ask.enqueue_answer(conn, q(conn, klass, ada, "What is DNA?").id)
    ask.enqueue_answer(conn, q(conn, klass, ben, "What is DNA?").id)
    assert ask.answer_pending(conn, p) == 2
    assert len(p.calls) == 1
