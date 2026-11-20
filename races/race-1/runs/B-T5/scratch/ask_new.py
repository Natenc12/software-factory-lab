"""Answering questions from the class's own material.

The answer depends on the question AND its class: the provider only ever sees the material of
the class the question was asked in, so the same words asked in two classes can get two
different answers.

Answers are cached in memory, per process, per class and question text: a repeat question in the
same class is answered without calling the provider, as long as the class's material (and the
provider) are the same as when the cached answer was made.
"""

from __future__ import annotations

import hashlib
import sqlite3

from lab.classes import get_class
from lab.db import now
from lab.jobs import enqueue, run_next
from lab.models import Answer
from lab.providers import Provider, get_provider
from lab.questions import get_question

ANSWER_JOB = "answer"

# (class id, question text exactly as stored) -> ((material fingerprint, provider name), body)
_answer_cache: dict[tuple[int, str], tuple[tuple[str, str], str]] = {}


def clear_answer_cache() -> None:
    """Empty the answer cache, so the next answer for any question calls the provider."""
    _answer_cache.clear()


def _fingerprint(material: str) -> str:
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def answer(conn: sqlite3.Connection, question_id: int, provider: Provider | None = None) -> Answer:
    """Answer a question from its class's material and store the answer (replacing any old one).

    A cached answer for the same text in the same class is reused, skipping the provider call,
    while the class's material and the provider are unchanged.
    """
    provider = provider or get_provider()
    question = get_question(conn, question_id)
    if question.hidden:
        raise ValueError(f"question {question_id} is hidden")
    material = get_class(conn, question.class_id).material
    key = (question.class_id, question.text)
    made_from = (_fingerprint(material), provider.name)
    cached = _answer_cache.get(key)
    if cached is not None and cached[0] == made_from:
        body = cached[1]
    else:
        body = provider.answer(question.text, material)
        _answer_cache[key] = (made_from, body)
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
