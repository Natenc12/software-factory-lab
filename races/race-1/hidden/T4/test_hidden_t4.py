"""Hidden tests for T4 (summary total). Copied into the lab's tests/ folder; uses its conftest.

Only class-level numbers are checked: student_breakdown is out of scope (and has a known bug for
students with no questions), so per-student rows are not asserted here.
"""

from lab import ask, classes, questions
from lab.summary import class_summary


def totals(conn, class_id):
    s = class_summary(conn, class_id)
    return s["total"], s["answered"], s["unanswered"]


def test_t4_one_visible_one_hidden_answered(conn, biology):
    klass, ada, _ = biology
    questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    gone = questions.ask_question(conn, klass.id, ada.id, "What is RNA?")
    ask.answer(conn, gone.id)
    questions.hide_question(conn, gone.id)
    assert totals(conn, klass.id) == (1, 0, 1)


def test_t4_three_visible_two_hidden(conn, biology):
    klass, ada, ben = biology
    v1 = questions.ask_question(conn, klass.id, ada.id, "What do mitochondria do?")
    questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    questions.ask_question(conn, klass.id, ben.id, "How does photosynthesis work?")
    h1 = questions.ask_question(conn, klass.id, ben.id, "Hidden one?")
    h2 = questions.ask_question(conn, klass.id, ada.id, "Hidden two?")
    ask.answer(conn, v1.id)
    ask.answer(conn, h1.id)
    questions.hide_question(conn, h1.id)
    questions.hide_question(conn, h2.id)
    assert totals(conn, klass.id) == (3, 1, 2)


def test_t4_all_hidden(conn, biology):
    klass, ada, _ = biology
    for text in ("A?", "B?"):
        questions.hide_question(conn, questions.ask_question(conn, klass.id, ada.id, text).id)
    assert totals(conn, klass.id) == (0, 0, 0)


def test_t4_no_questions(conn, biology):
    klass, _, _ = biology
    assert totals(conn, klass.id) == (0, 0, 0)


def test_t4_no_hidden_unchanged(conn, biology):
    klass, ada, ben = biology
    q1 = questions.ask_question(conn, klass.id, ada.id, "What do mitochondria do?")
    questions.ask_question(conn, klass.id, ben.id, "What is DNA?")
    ask.answer(conn, q1.id)
    assert totals(conn, klass.id) == (2, 1, 1)


def test_t4_hidden_in_other_class_ignored(conn, biology):
    klass, ada, _ = biology
    art = classes.create_class(conn, "Art")
    carl = classes.enrol_student(conn, art.id, "Carl")
    questions.hide_question(conn, questions.ask_question(conn, art.id, carl.id, "Blue?").id)
    questions.ask_question(conn, art.id, carl.id, "Red?")
    questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    assert totals(conn, klass.id) == (1, 0, 1)
    assert totals(conn, art.id) == (1, 0, 1)


def test_t4_shape_unchanged(conn, biology):
    klass, ada, _ = biology
    questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    s = class_summary(conn, klass.id)
    assert set(s) == {"class_id", "name", "total", "answered", "unanswered", "students"}
    assert s["class_id"] == klass.id and s["name"] == "Biology"
    assert set(s["students"][0]) == {"student_id", "name", "questions", "answered", "unanswered"}
