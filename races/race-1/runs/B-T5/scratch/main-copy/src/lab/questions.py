"""Students' questions: asking, hiding, and listing them a page at a time."""

from __future__ import annotations

import sqlite3

from lab.classes import get_student
from lab.db import now
from lab.models import Question


def ask_question(
    conn: sqlite3.Connection,
    class_id: int,
    student_id: int,
    text: str,
    asked_at: str | None = None,
) -> Question:
    """Record a question from a student enrolled in the class."""
    student = get_student(conn, student_id)
    if student.class_id != class_id:
        raise ValueError(f"student {student_id} is not enrolled in class {class_id}")
    text = text.strip()
    if not text:
        raise ValueError("a question needs some text")
    cur = conn.execute(
        "insert into questions (class_id, student_id, text, asked_at) values (?, ?, ?, ?)",
        (class_id, student_id, text, asked_at or now()),
    )
    conn.commit()
    return get_question(conn, cur.lastrowid)


def get_question(conn: sqlite3.Connection, question_id: int) -> Question:
    row = conn.execute("select * from questions where id = ?", (question_id,)).fetchone()
    if row is None:
        raise LookupError(f"no question with id {question_id}")
    return Question.from_row(row)


def hide_question(conn: sqlite3.Connection, question_id: int) -> None:
    """Remove a question from lists and counts. The row is kept."""
    get_question(conn, question_id)
    conn.execute("update questions set hidden = 1 where id = ?", (question_id,))
    conn.commit()


def count_questions(conn: sqlite3.Connection, class_id: int) -> int:
    """How many visible questions the class has."""
    row = conn.execute(
        "select count(*) from questions where class_id = ? and hidden = 0", (class_id,)
    ).fetchone()
    return row[0]


def list_questions(
    conn: sqlite3.Connection, class_id: int, page: int = 1, per_page: int = 20
) -> list[Question]:
    """One page of a class's visible questions, oldest first. Pages start at 1."""
    if page < 1:
        raise ValueError("page starts at 1")
    if per_page < 1:
        raise ValueError("per_page must be at least 1")
    first_row = (page - 1) * per_page
    rows = conn.execute(
        "select * from questions where class_id = ? and hidden = 0 order by id limit ? offset ?",
        (class_id, per_page, max(first_row - 1, 0)),
    ).fetchall()
    return [Question.from_row(row) for row in rows]
