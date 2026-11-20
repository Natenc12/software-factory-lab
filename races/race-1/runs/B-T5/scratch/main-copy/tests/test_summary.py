from lab import ask, classes, questions
from lab.summary import class_summary


def test_empty_class(conn, biology):
    klass, _, _ = biology
    s = class_summary(conn, klass.id)
    assert (s["total"], s["answered"], s["unanswered"]) == (0, 0, 0)
    assert [st["name"] for st in s["students"]] == ["Ada", "Ben"]


def test_counts_per_student_and_class(conn, biology):
    klass, ada, ben = biology
    q1 = questions.ask_question(conn, klass.id, ada.id, "What do mitochondria do?")
    questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    questions.ask_question(conn, klass.id, ben.id, "How does photosynthesis work?")
    ask.answer(conn, q1.id)

    s = class_summary(conn, klass.id)
    assert s["name"] == "Biology"
    assert (s["total"], s["answered"], s["unanswered"]) == (3, 1, 2)
    assert s["students"] == [
        {"student_id": ada.id, "name": "Ada", "questions": 2, "answered": 1, "unanswered": 1},
        {"student_id": ben.id, "name": "Ben", "questions": 1, "answered": 0, "unanswered": 1},
    ]


def test_other_classes_do_not_leak_in(conn, biology):
    klass, ada, _ = biology
    other = classes.create_class(conn, "Art")
    carl = classes.enrol_student(conn, other.id, "Carl")
    questions.ask_question(conn, other.id, carl.id, "What is blue?")
    questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    s = class_summary(conn, klass.id)
    assert s["total"] == 1
    assert [st["name"] for st in s["students"]] == ["Ada", "Ben"]
