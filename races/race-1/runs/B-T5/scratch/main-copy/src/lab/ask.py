"""Answering questions from the class's own material.

The answer depends on the question AND its class: the provider only ever sees the material of
the class the question was asked in, so the same words asked in two classes can get two
different answers.
"""

from __future__ import annotations

import sqlite3

from lab.classes import get_class
from lab.db import now
from lab.jobs import enqueue, run_next
from lab.models import Answer
from lab.providers import Provider, get_provider
from lab.questions import get_question

ANSWER_JOB = "answer"


def answer(conn: sqlite3.Connection, question_id: int, provider: Provider | None = None) -> Answer:
    """Answer a question from its class's material and store the answer (replacing any old one)."""
    provider = provider or get_provider()
    question = get_question(conn, question_id)
    if question.hidden:
        raise ValueError(f"question {question_id} is hidden")
    material = get_class(conn, question.class_id).material
    body = provider.answer(question.text, material)
    conn.execute(
        """
        insert into answers (question_id, body, provider, created_at) values (?, ?, ?, ?)
        on conflict (question_id) do update
            set body = excluded.body, provider = excluded.provider,
                created_at = excluded.created_at
        """,
        (question_id, body, provider.name, now()),
    )
    conn.commit()
    return get_answer(conn, question_id)


def get_answer(conn: sqlite3.Connection, question_id: int) -> Answer | None:
    row = conn.execute("select * from answers where question_id = ?", (question_id,)).fetchone()
    return None if row is None else Answer.from_row(row)


def enqueue_answer(conn: sqlite3.Connection, question_id: int) -> int:
    """Queue a question to be answered by `answer_pending`. Returns the job id."""
    get_question(conn, question_id)
    return enqueue(conn, ANSWER_JOB, {"question_id": question_id})


def answer_pending(conn: sqlite3.Connection, provider: Provider | None = None) -> int:
    """Work the queue until it is empty. Returns how many jobs ran (done or failed)."""
    provider = provider or get_provider()

    def handle(conn: sqlite3.Connection, payload: dict) -> None:
        answer(conn, payload["question_id"], provider)

    ran = 0
    while run_next(conn, {ANSWER_JOB: handle}) is not None:
        ran += 1
    return ran
