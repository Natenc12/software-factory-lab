"""A class at a glance: how many questions, and how many are still waiting for an answer."""

from __future__ import annotations

import sqlite3

from lab.classes import get_class


def class_summary(conn: sqlite3.Connection, class_id: int) -> dict:
    """Totals for the class and a per-student breakdown. Hidden questions are not counted.

    Returns:
        {"class_id": 1, "name": "Biology", "total": 5, "answered": 3, "unanswered": 2,
         "students": [{"student_id": 1, "name": "Ada", "questions": 2, "answered": 1,
                       "unanswered": 1}, ...]}
    """
    klass = get_class(conn, class_id)
    total = conn.execute(
        "select count(*) from questions where class_id = ?", (class_id,)
    ).fetchone()[0]
    answered = conn.execute(
        "select count(*) from questions q join answers a on a.question_id = q.id"
        " where q.class_id = ? and q.hidden = 0",
        (class_id,),
    ).fetchone()[0]
    return {
        "class_id": klass.id,
        "name": klass.name,
        "total": total,
        "answered": answered,
        "unanswered": total - answered,
        "students": student_breakdown(conn, class_id),
    }


def student_breakdown(conn: sqlite3.Connection, class_id: int) -> list[dict]:
    """One entry per enrolled student, including students who have asked nothing yet."""
    rows = conn.execute(
        """
        select s.id as student_id, s.name as name,
               count(*) as questions, count(a.id) as answered
        from students s
        left join questions q on q.student_id = s.id and q.hidden = 0
        left join answers a on a.question_id = q.id
        where s.class_id = ?
        group by s.id
        order by s.name, s.id
        """,
        (class_id,),
    ).fetchall()
    return [
        {
            "student_id": row["student_id"],
            "name": row["name"],
            "questions": row["questions"],
            "answered": row["answered"],
            "unanswered": row["questions"] - row["answered"],
        }
        for row in rows
    ]
