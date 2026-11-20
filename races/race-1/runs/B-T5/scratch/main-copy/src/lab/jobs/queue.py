"""A tiny job queue on the `jobs` table: enqueue, claim, done, fail.

A job moves pending -> running -> done or failed. `claim` takes the oldest pending job and
marks it running in one guarded update, so two workers never get the same job.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from lab.db import now

Handler = Callable[[sqlite3.Connection, dict], None]


@dataclass(frozen=True)
class Job:
    id: int
    kind: str
    payload: dict
    status: str
    attempts: int
    error: str | None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Job:
        return cls(
            row["id"],
            row["kind"],
            json.loads(row["payload"]),
            row["status"],
            row["attempts"],
            row["error"],
        )


def enqueue(conn: sqlite3.Connection, kind: str, payload: dict | None = None) -> int:
    """Add a pending job and return its id."""
    stamp = now()
    cur = conn.execute(
        "insert into jobs (kind, payload, created_at, updated_at) values (?, ?, ?, ?)",
        (kind, json.dumps(payload or {}), stamp, stamp),
    )
    conn.commit()
    return cur.lastrowid


def get_job(conn: sqlite3.Connection, job_id: int) -> Job:
    row = conn.execute("select * from jobs where id = ?", (job_id,)).fetchone()
    if row is None:
        raise LookupError(f"no job with id {job_id}")
    return Job.from_row(row)


def claim(conn: sqlite3.Connection) -> Job | None:
    """Mark the oldest pending job running and return it, or None if there is none."""
    while True:
        row = conn.execute(
            "select id from jobs where status = 'pending' order by id limit 1"
        ).fetchone()
        if row is None:
            return None
        cur = conn.execute(
            "update jobs set status = 'running', attempts = attempts + 1, updated_at = ?"
            " where id = ? and status = 'pending'",
            (now(), row["id"]),
        )
        conn.commit()
        if cur.rowcount == 1:
            return get_job(conn, row["id"])
        # Another worker claimed it between the select and the update: try the next one.


def done(conn: sqlite3.Connection, job_id: int) -> None:
    _finish(conn, job_id, "done", None)


def fail(conn: sqlite3.Connection, job_id: int, error: str) -> None:
    _finish(conn, job_id, "failed", error)


def _finish(conn: sqlite3.Connection, job_id: int, status: str, error: str | None) -> None:
    cur = conn.execute(
        "update jobs set status = ?, error = ?, updated_at = ? where id = ? and status = 'running'",
        (status, error, now(), job_id),
    )
    conn.commit()
    if cur.rowcount != 1:
        raise ValueError(f"job {job_id} is not running")


def run_next(conn: sqlite3.Connection, handlers: dict[str, Handler]) -> Job | None:
    """Claim one job and run its handler. Returns the finished job, or None if the queue is empty.

    A handler that raises marks the job failed with the error text; it does not stop the worker.
    """
    job = claim(conn)
    if job is None:
        return None
    handler = handlers.get(job.kind)
    if handler is None:
        fail(conn, job.id, f"no handler for job kind {job.kind!r}")
        return get_job(conn, job.id)
    try:
        handler(conn, job.payload)
    except Exception as err:  # any handler error fails the job, not the worker
        conn.rollback()
        fail(conn, job.id, f"{type(err).__name__}: {err}")
    else:
        done(conn, job.id)
    return get_job(conn, job.id)
