import os, importlib.util, sqlite3
from pathlib import Path
from lab.db import connect
from lab import classes, questions
from lab.ask import answer, clear_answer_cache, get_answer, enqueue_answer, answer_pending, _answer_cache
from lab.providers import FakeProvider
spec = importlib.util.spec_from_file_location("m", "scripts/migrate.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
db = os.environ["LAB_DB"]
for p in [db]:
    if Path(p).exists(): os.remove(p)
import subprocess; subprocess.run(["uv","run","python","scripts/migrate.py"],check=True,capture_output=True)
conn = connect(db) if 'path' not in connect.__code__.co_varnames or True else None
class C:
    def __init__(s,name="counting"): s.calls=0; s.name=name
    def answer(s,q,mat): s.calls+=1; return FakeProvider().answer(q,mat)
bio = classes.create_class(conn,"Bio","DNA carries genetic information. Mitochondria make energy.")
a = classes.enrol_student(conn,bio.id,"Ada"); b = classes.enrol_student(conn,bio.id,"Ben")
p=C()
q1=questions.ask_question(conn,bio.id,a.id,"What is DNA?"); q2=questions.ask_question(conn,bio.id,b.id,"What is DNA?")
r1=answer(conn,q1.id,p); r2=answer(conn,q2.id,p)
print("1 same text calls:",p.calls, "| 2 rows:", conn.execute("select question_id,body from answers order by question_id").fetchall())
answer(conn,q1.id,p); print("6 re-answer rows:",conn.execute("select count(*) from answers").fetchone()[0],"calls",p.calls)
clear_answer_cache(); answer(conn,q1.id,p); print("3 after clear calls:",p.calls)
# 4 two classes
cook=classes.create_class(conn,"Cook","Energy comes from oats.")
c=classes.enrol_student(conn,cook.id,"Cora"); p=C()
x=answer(conn,questions.ask_question(conn,bio.id,a.id,"Where does energy come from?").id,p)
y=answer(conn,questions.ask_question(conn,cook.id,c.id,"Where does energy come from?").id,p)
print("4 two classes calls:",p.calls, x.body,"|",y.body)
# 5 A->B->A
clear_answer_cache(); p=C(); t="What carries genetic information?"
orig=bio.material
r=[]
for mat in [None,"Genes carry genetic information too.",orig]:
    if mat: classes.set_material(conn,bio.id,mat)
    r.append(answer(conn,questions.ask_question(conn,bio.id,a.id,t).id,p).body)
print("5 A->B->A calls:",p.calls, r)
# set_material with identical text
n=p.calls; classes.set_material(conn,bio.id,orig); answer(conn,questions.ask_question(conn,bio.id,a.id,t).id,p); print("5b identical set_material, provider called again?", p.calls>n)
# queue
clear_answer_cache(); p=C()
qa=questions.ask_question(conn,bio.id,a.id,"Why mitochondria?"); qb=questions.ask_question(conn,bio.id,b.id,"Why mitochondria?")
enqueue_answer(conn,qa.id); enqueue_answer(conn,qb.id); print("6 queue ran",answer_pending(conn,p),"calls",p.calls)
# provider name on hit with different provider
other=C("other"); qc=questions.ask_question(conn,bio.id,a.id,"Why mitochondria?"); print("hit w/ other provider: stored provider =",answer(conn,qc.id,other).provider,"other.calls",other.calls)
# hidden question with cached text
qh=questions.ask_question(conn,bio.id,a.id,"Why mitochondria?"); questions.hide_question(conn,qh.id)
try: answer(conn,qh.id,p); print("hidden answered!")
except ValueError as e: print("hidden refused:",e)
# missing question
try: answer(conn,99999,p)
except LookupError as e: print("missing:",e)
print("tables:",[r[0] for r in conn.execute("select name from sqlite_master where type='table'")])
