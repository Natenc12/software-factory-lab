"""Hidden tests for T1 (pagination). Copied into the lab's tests/ folder."""

import pytest

from lab import classes, questions


def ask_many(conn, klass, student, n):
    return [questions.ask_question(conn, klass.id, student.id, f"Hidden T1 {i}?") for i in range(n)]


def all_pages(conn, class_id, per_page, upto):
    return [questions.list_questions(conn, class_id, page=p, per_page=per_page) for p in upto]


def test_t1_seven_questions_three_per_page(conn, biology):
    klass, ada, _ = biology
    q = ask_many(conn, klass, ada, 7)
    pages = all_pages(conn, klass.id, 3, (1, 2, 3, 4))
    assert pages == [q[0:3], q[3:6], q[6:7], []]


@pytest.mark.parametrize("n,per_page", [(1, 1), (4, 1), (5, 2), (6, 3), (10, 4), (20, 7), (3, 20)])
def test_t1_pages_are_disjoint_and_complete(conn, biology, n, per_page):
    klass, ada, _ = biology
    asked = ask_many(conn, klass, ada, n)
    n_pages = -(-n // per_page)
    pages = all_pages(conn, klass.id, per_page, range(1, n_pages + 2))
    flat = [x for page in pages for x in page]
    assert flat == asked
    assert len({x.id for x in flat}) == n
    assert pages[-1] == []
    assert all(len(p) == per_page for p in pages[:-2])


def test_t1_hidden_questions_do_not_shift_pages(conn, biology):
    klass, ada, _ = biology
    q = ask_many(conn, klass, ada, 6)
    questions.hide_question(conn, q[1].id)
    pages = all_pages(conn, klass.id, 2, (1, 2, 3, 4))
    assert pages == [[q[0], q[2]], [q[3], q[4]], [q[5]], []]


def test_t1_default_page_size_and_first_page(conn, biology):
    klass, ada, _ = biology
    q = ask_many(conn, klass, ada, 25)
    assert questions.list_questions(conn, klass.id) == q[:20]
    assert questions.list_questions(conn, klass.id, page=2) == q[20:]


def test_t1_other_classes_do_not_appear(conn, biology):
    klass, ada, _ = biology
    art = classes.create_class(conn, "Art")
    carl = classes.enrol_student(conn, art.id, "Carl")
    mine = []
    for i in range(5):
        mine.append(questions.ask_question(conn, klass.id, ada.id, f"Bio {i}?"))
        questions.ask_question(conn, art.id, carl.id, f"Art {i}?")
    pages = all_pages(conn, klass.id, 2, (1, 2, 3))
    assert [x for p in pages for x in p] == mine


def test_t1_bad_arguments_still_raise(conn, biology):
    klass, _, _ = biology
    with pytest.raises(ValueError):
        questions.list_questions(conn, klass.id, page=0)
    with pytest.raises(ValueError):
        questions.list_questions(conn, klass.id, per_page=0)
