"""Plain records for the app's four tables. Each one is built straight from a database row."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Class:
    id: int
    name: str
    material: str
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Class:
        return cls(row["id"], row["name"], row["material"], row["created_at"])


@dataclass(frozen=True)
class Student:
    id: int
    class_id: int
    name: str
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Student:
        return cls(row["id"], row["class_id"], row["name"], row["created_at"])


@dataclass(frozen=True)
class Question:
    id: int
    class_id: int
    student_id: int
    text: str
    hidden: bool
    asked_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Question:
        return cls(
            row["id"],
            row["class_id"],
            row["student_id"],
            row["text"],
            bool(row["hidden"]),
            row["asked_at"],
        )


@dataclass(frozen=True)
class Answer:
    id: int
    question_id: int
    body: str
    provider: str
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Answer:
        return cls(row["id"], row["question_id"], row["body"], row["provider"], row["created_at"])
