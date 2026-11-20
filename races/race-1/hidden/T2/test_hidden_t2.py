"""Hidden tests for T2 (CSV export). Copied into the lab's tests/ folder."""

import csv
import io

import pytest

from lab import ask, classes, questions

HEADER = "question_id,student,asked_at,question,answer\n"


def export(conn, class_id):
    from lab.export import export_class_questions

    return export_class_questions(conn, class_id)


def test_t2_worked_example_exact(conn, biology):
    klass, ada, ben = biology
    q1 = questions.ask_question(conn, klass.id, ada.id, "What is DNA?", "2026-03-01T09:00:00")
    q2 = questions.ask_question(conn, klass.id, ben.id, "Why, though?", "2026-03-01T09:05:00")
    q3 = questions.ask_question(
        conn, klass.id, ada.id, 'What does "ATP" mean?', "2026-03-01T09:10:00"
    )
    q4 = questions.ask_question(
        conn, klass.id, ben.id, "Is this on the test?", "2026-03-01T09:15:00"
    )
    ask.answer(conn, q1.id)
    questions.hide_question(conn, q4.id)
    expected = (
        HEADER
        + f"{q1.id},Ada,2026-03-01T09:00:00,What is DNA?,"
        + "From the class material: DNA carries genetic information.\n"
        + f'{q2.id},Ben,2026-03-01T09:05:00,"Why, though?",\n'
        + f'{q3.id},Ada,2026-03-01T09:10:00,"What does ""ATP"" mean?",\n'
    )
    out = export(conn, klass.id)
    assert isinstance(out, str)
    assert out == expected


def test_t2_empty_class_is_header_only(conn, biology):
    klass, _, _ = biology
    assert export(conn, klass.id) == HEADER


def test_t2_only_hidden_questions_is_header_only(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "Gone?")
    questions.hide_question(conn, q.id)
    assert export(conn, klass.id) == HEADER


def test_t2_unknown_class_raises_lookup_error(conn):
    with pytest.raises(LookupError):
        export(conn, 999)


def test_t2_other_classes_left_out_and_ordered_by_id(conn, biology):
    klass, ada, ben = biology
    art = classes.create_class(conn, "Art")
    carl = classes.enrol_student(conn, art.id, "Carl")
    a = questions.ask_question(conn, klass.id, ada.id, "First?", "2026-03-05T00:00:00")
    questions.ask_question(conn, art.id, carl.id, "What is blue?", "2026-03-01T00:00:00")
    b = questions.ask_question(conn, klass.id, ben.id, "Second?", "2026-03-02T00:00:00")
    rows = list(csv.reader(io.StringIO(export(conn, klass.id))))
    assert rows == [
        ["question_id", "student", "asked_at", "question", "answer"],
        [str(a.id), "Ada", "2026-03-05T00:00:00", "First?", ""],
        [str(b.id), "Ben", "2026-03-02T00:00:00", "Second?", ""],
    ]


def test_t2_line_breaks_and_quotes_round_trip(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "Line one\nline two", "2026-03-01T09:00:00")
    out = export(conn, klass.id)
    assert out == HEADER + f'{q.id},Ada,2026-03-01T09:00:00,"Line one\nline two",\n'
    assert "\r" not in out


def test_t2_answer_column_uses_latest_stored_answer(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "What carries genetic information?")
    ask.answer(conn, q.id)
    classes.set_material(conn, klass.id, "Genes carry genetic information, plain and simple.")
    ask.answer(conn, q.id)
    rows = list(csv.reader(io.StringIO(export(conn, klass.id))))
    assert (
        rows[1][4] == "From the class material: Genes carry genetic information, plain and simple."
    )
    assert len(rows) == 2
