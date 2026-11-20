import pytest

from lab import classes, questions


def ask_many(conn, klass, student, n):
    return [questions.ask_question(conn, klass.id, student.id, f"Question {i}?") for i in range(n)]


def test_ask_question(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "  What is DNA? ", "2026-01-02T03:04:05")
    assert q.text == "What is DNA?"
    assert q.asked_at == "2026-01-02T03:04:05"
    assert q.hidden is False
    assert questions.get_question(conn, q.id) == q


def test_question_needs_text(conn, biology):
    klass, ada, _ = biology
    with pytest.raises(ValueError):
        questions.ask_question(conn, klass.id, ada.id, " ")


def test_student_must_be_in_the_class(conn, biology):
    _, ada, _ = biology
    other = classes.create_class(conn, "Art")
    with pytest.raises(ValueError, match="not enrolled"):
        questions.ask_question(conn, other.id, ada.id, "Why?")


def test_first_page(conn, biology):
    klass, ada, _ = biology
    asked = ask_many(conn, klass, ada, 5)
    assert questions.list_questions(conn, klass.id, page=1, per_page=3) == asked[:3]


def test_page_past_the_end_is_empty(conn, biology):
    klass, ada, _ = biology
    ask_many(conn, klass, ada, 2)
    assert questions.list_questions(conn, klass.id, page=5, per_page=3) == []


def test_bad_page_arguments(conn, biology):
    klass, _, _ = biology
    with pytest.raises(ValueError):
        questions.list_questions(conn, klass.id, page=0)
    with pytest.raises(ValueError):
        questions.list_questions(conn, klass.id, per_page=0)


def test_list_is_per_class(conn, biology):
    klass, ada, _ = biology
    other = classes.create_class(conn, "Art")
    carl = classes.enrol_student(conn, other.id, "Carl")
    mine = ask_many(conn, klass, ada, 2)
    questions.ask_question(conn, other.id, carl.id, "What is blue?")
    assert questions.list_questions(conn, klass.id) == mine


def test_hidden_questions_are_not_listed_or_counted(conn, biology):
    klass, ada, _ = biology
    first, second = ask_many(conn, klass, ada, 2)
    questions.hide_question(conn, first.id)
    assert questions.list_questions(conn, klass.id) == [second]
    assert questions.count_questions(conn, klass.id) == 1
    assert questions.get_question(conn, first.id).hidden is True
