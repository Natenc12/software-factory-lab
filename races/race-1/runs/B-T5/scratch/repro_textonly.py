"""Play the contract as written (cache keyed by question text only) against origin/main's code."""
import os, sys, importlib.util
root = sys.argv[1]
os.environ["LAB_DB"] = sys.argv[2]
sys.path.insert(0, root + "/src")
spec = importlib.util.spec_from_file_location("migrate", root + "/scripts/migrate.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.migrate()
from lab import classes, questions, ask
from lab.db import connect
from lab.providers import FakeProvider

cache = {}
class TextOnlyCache:  # wraps the provider: what a text-keyed cache in answer() does
    name = "fake"
    def __init__(self): self.inner = FakeProvider(); self.calls = 0
    def answer(self, q, material):
        if q not in cache:
            self.calls += 1; cache[q] = self.inner.answer(q, material)
        return cache[q]

conn = connect()
p = TextOnlyCache()
bio = classes.create_class(conn, "Biology", "Mitochondria produce energy for the cell. DNA carries genetic information.")
ada = classes.enrol_student(conn, bio.id, "Ada")
cook = classes.create_class(conn, "Cooking", "Energy for a long day comes from oats.")
cora = classes.enrol_student(conn, cook.id, "Cora")
t = "Where does energy come from?"
a1 = ask.answer(conn, questions.ask_question(conn, bio.id, ada.id, t).id, p)
a2 = ask.answer(conn, questions.ask_question(conn, cook.id, cora.id, t).id, p)
print("1) same text, two classes")
print("   Biology:", a1.body)
print("   Cooking:", a2.body, " <- without the cache:", FakeProvider().answer(t, cook.material))
q = questions.ask_question(conn, bio.id, ada.id, "What carries genetic information?")
ask.answer(conn, q.id, p)
classes.set_material(conn, bio.id, "Genes carry genetic information too.")
print("2) after set_material")
print("   answer():", ask.answer(conn, q.id, p).body, " <- without the cache:", FakeProvider().answer(q.text, "Genes carry genetic information too."))
