"""Classes and the students enrolled in them."""

from __future__ import annotations

import sqlite3

from lab.db import now
from lab.models import Class, Student


def create_class(conn: sqlite3.Connection, name: str, material: str = "") -> Class:
    """Create a class. `material` is the course text answers are drawn from."""
    name = name.strip()
    if not name:
        raise ValueError("a class needs a name")
    cur = conn.execute(
        "insert into classes (name, material, created_at) values (?, ?, ?)",
        (name, material, now()),
    )
    conn.commit()
    return get_class(conn, cur.lastrowid)


def get_class(conn: sqlite3.Connection, class_id: int) -> Class:
    row = conn.execute("select * from classes where id = ?", (class_id,)).fetchone()
    if row is None:
        raise LookupError(f"no class with id {class_id}")
    return Class.from_row(row)


def list_classes(conn: sqlite3.Connection) -> list[Class]:
    rows = conn.execute("select * from classes order by name, id").fetchall()
    return [Class.from_row(row) for row in rows]


def set_material(conn: sqlite3.Connection, class_id: int, material: str) -> Class:
    """Replace a class's material. Later answers use the new text."""
    get_class(conn, class_id)
    conn.execute("update classes set material = ? where id = ?", (material, class_id))
    conn.commit()
    return get_class(conn, class_id)


def enrol_student(conn: sqlite3.Connection, class_id: int, name: str) -> Student:
    """Add a student to a class. Names are unique within a class."""
    get_class(conn, class_id)
    name = name.strip()
    if not name:
        raise ValueError("a student needs a name")
    cur = conn.execute(
        "insert into students (class_id, name, created_at) values (?, ?, ?)",
        (class_id, name, now()),
    )
    conn.commit()
    return get_student(conn, cur.lastrowid)


def get_student(conn: sqlite3.Connection, student_id: int) -> Student:
    row = conn.execute("select * from students where id = ?", (student_id,)).fetchone()
    if row is None:
        raise LookupError(f"no student with id {student_id}")
    return Student.from_row(row)


def list_students(conn: sqlite3.Connection, class_id: int) -> list[Student]:
    rows = conn.execute(
        "select * from students where class_id = ? order by name, id", (class_id,)
    ).fetchall()
    return [Student.from_row(row) for row in rows]
