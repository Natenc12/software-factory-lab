import pytest

from lab.jobs import claim, done, enqueue, fail, get_job, run_next


def test_enqueue_and_claim_oldest_first(conn):
    first = enqueue(conn, "demo", {"n": 1})
    enqueue(conn, "demo", {"n": 2})
    job = claim(conn)
    assert (job.id, job.status, job.attempts, job.payload) == (first, "running", 1, {"n": 1})


def test_claim_on_empty_queue_returns_none(conn):
    assert claim(conn) is None


def test_a_job_is_claimed_only_once(conn):
    enqueue(conn, "demo")
    assert claim(conn) is not None
    assert claim(conn) is None


def test_done_and_fail(conn):
    a, b = enqueue(conn, "demo"), enqueue(conn, "demo")
    claim(conn)
    claim(conn)
    done(conn, a)
    fail(conn, b, "boom")
    assert get_job(conn, a).status == "done"
    assert (get_job(conn, b).status, get_job(conn, b).error) == ("failed", "boom")


def test_cannot_finish_a_job_that_is_not_running(conn):
    job_id = enqueue(conn, "demo")
    with pytest.raises(ValueError):
        done(conn, job_id)


def test_run_next_runs_the_handler(conn):
    seen = []
    enqueue(conn, "demo", {"x": 3})
    job = run_next(conn, {"demo": lambda c, payload: seen.append(payload["x"])})
    assert job.status == "done"
    assert seen == [3]
    assert run_next(conn, {}) is None


def test_run_next_fails_on_error_or_unknown_kind(conn):
    def boom(c, payload):
        raise RuntimeError("nope")

    enqueue(conn, "demo")
    enqueue(conn, "mystery")
    assert run_next(conn, {"demo": boom}).error == "RuntimeError: nope"
    assert "no handler" in run_next(conn, {"demo": boom}).error
