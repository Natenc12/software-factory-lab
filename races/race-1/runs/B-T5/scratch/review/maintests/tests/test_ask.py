import pytest

from lab import classes, questions
from lab.ask import answer, answer_pending, enqueue_answer, get_answer
from lab.jobs import get_job
from lab.providers import FakeProvider, get_provider
from lab.providers.fake import NOT_FOUND


def test_fake_provider_is_deterministic_and_uses_material():
    p = FakeProvider()
    material = "Cats purr. Dogs bark loudly at night."
    assert p.answer("Why do dogs bark?", material) == p.answer("Why do dogs bark?", material)
    assert p.answer("Why do dogs bark?", material).endswith("Dogs bark loudly at night.")
    assert p.answer("What is calculus?", material) == NOT_FOUND


def test_get_provider():
    assert get_provider().name == "fake"
    with pytest.raises(ValueError):
        get_provider("real")


def test_answer_from_class_material(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "What do mitochondria produce?")
    a = answer(conn, q.id)
    assert "Mitochondria produce energy" in a.body
    assert a.provider == "fake"
    assert get_answer(conn, q.id) == a


def test_same_question_in_two_classes_gets_each_class_answer(conn, biology):
    klass, ada, _ = biology
    cooking = classes.create_class(conn, "Cooking", "Energy for a long day comes from oats.")
    cora = classes.enrol_student(conn, cooking.id, "Cora")
    text = "Where does energy come from?"
    bio_answer = answer(conn, questions.ask_question(conn, klass.id, ada.id, text).id)
    cook_answer = answer(conn, questions.ask_question(conn, cooking.id, cora.id, text).id)
    assert "Mitochondria" in bio_answer.body
    assert "oats" in cook_answer.body


def test_answering_again_replaces_the_answer(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "What carries genetic information?")
    answer(conn, q.id)
    classes.set_material(conn, klass.id, "Genes carry genetic information too.")
    assert "Genes" in answer(conn, q.id).body
    assert conn.execute("select count(*) from answers").fetchone()[0] == 1


def test_answer_uses_given_provider(conn, biology):
    klass, ada, _ = biology

    class Echo:
        name = "echo"

        def answer(self, question, material):
            return f"{question} | {len(material)}"

    q = questions.ask_question(conn, klass.id, ada.id, "Hi?")
    a = answer(conn, q.id, Echo())
    assert a.provider == "echo"
    assert a.body == f"Hi? | {len(klass.material)}"


def test_hidden_or_missing_question_is_not_answered(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    questions.hide_question(conn, q.id)
    with pytest.raises(ValueError):
        answer(conn, q.id)
    with pytest.raises(LookupError):
        answer(conn, 999)


def test_queued_answers(conn, biology):
    klass, ada, _ = biology
    q1 = questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    q2 = questions.ask_question(conn, klass.id, ada.id, "What is photosynthesis?")
    jobs = [enqueue_answer(conn, q1.id), enqueue_answer(conn, q2.id)]
    assert answer_pending(conn) == 2
    assert [get_job(conn, j).status for j in jobs] == ["done", "done"]
    assert get_answer(conn, q2.id).body.endswith(
        "Photosynthesis turns sunlight into sugar in plants."
    )


def test_queued_answer_for_hidden_question_fails_the_job(conn, biology):
    klass, ada, _ = biology
    q = questions.ask_question(conn, klass.id, ada.id, "What is DNA?")
    job_id = enqueue_answer(conn, q.id)
    questions.hide_question(conn, q.id)
    assert answer_pending(conn) == 1
    job = get_job(conn, job_id)
    assert job.status == "failed"
    assert "hidden" in job.error
