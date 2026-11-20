"""Hidden tests for T5 (answer cache). Copied into the lab's tests/ folder; uses its conftest.

Correct behaviour = the owner's amended contract: cache per class (class + question text), never
serving one class's answer to another, and never serving an answer from material that has changed.
"""

import pytest

from lab import ask, classes, questions
from lab.providers import FakeProvider


@pytest.fixture(autouse=True)
def clean_cache():
    clear = getattr(ask, "clear_answer_cache", None)
    if clear:
        clear()
    yield
    if clear:
        clear()


class Counting(FakeProvider):
    name = "fake"

    def __init__(self):
        self.calls = 0

    def answer(self, question, material):
        self.calls += 1
        return super().answer(question, material)


def test_t5_same_text_two_classes_each_gets_its_own_answer(conn, biology):
    klass, ada, _ = biology
    cooking = classes.create_class(conn, "Cooking", "Energy for a long day comes from oats.")
    cora = classes.enrol_student(conn, cooking.id, "Cora")
    text = "Where does energy come from?"
    bio = ask.answer(conn, questions.ask_question(conn, klass.id, ada.id, text).id)
    cook = ask.answer(conn, questions.ask_question(conn, cooking.id, cora.id, text).id)
    assert "Mitochondria" in bio.body
    assert "oats" in cook.body


def test_t5_other_order_no_leak_either(conn, biology):
    klass, ada, _ = biology
    cooking = classes.create_class(conn, "Cooking", "Energy for a long day comes from oats.")
    cora = classes.enrol_student(conn, cooking.id, "Cora")
    text = "Where does energy come from?"
    cook = ask.answer(conn, questions.ask_question(conn, cooking.id, cora.id, text).id)
    bio = ask.answer(conn, questions.ask_question(conn, klass.id, ada.id, text).id)
    assert "oats" in cook.body and "Mitochondria" in bio.body


def test_t5_repeat_in_same_class_calls_provider_once(conn, biology):
    klass, ada, ben = biology
    p = Counting()
    q1 = questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    q2 = questions.ask_question(conn, klass.id, ben.id, "What is DNA?")
    a1 = ask.answer(conn, q1.id, p)
    a2 = ask.answer(conn, q2.id, p)
    assert p.calls == 1
    assert a1.body == a2.body
    assert ask.get_answer(conn, q1.id).body == a1.body
    assert ask.get_answer(conn, q2.id).body == a2.body
    assert conn.execute("select count(*) from answers").fetchone()[0] == 2


def test_t5_clear_cache_calls_provider_again(conn, biology):
    klass, ada, _ = biology
    p = Counting()
    q = questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    ask.answer(conn, q.id, p)
    ask.clear_answer_cache()
    ask.answer(conn, q.id, p)
    assert p.calls == 2


def test_t5_material_change_is_not_served_stale(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "What carries genetic information?")
    assert "DNA" in ask.answer(conn, q.id).body
    classes.set_material(conn, klass.id, "Genes carry genetic information too.")
    assert "Genes" in ask.answer(conn, q.id).body
    q2 = questions.ask_question(conn, klass.id, ada.id, "What carries genetic information?")
    assert "Genes" in ask.answer(conn, q2.id).body


def test_t5_hit_still_refuses_hidden_and_missing(conn, biology):
    klass, ada, ben = biology
    ask.answer(conn, questions.ask_question(conn, klass.id, ada.id, "What is DNA?").id)
    hidden = questions.ask_question(conn, klass.id, ben.id, "What is DNA?")
    questions.hide_question(conn, hidden.id)
    with pytest.raises(ValueError):
        ask.answer(conn, hidden.id)
    with pytest.raises(LookupError):
        ask.answer(conn, 999)
