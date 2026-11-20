import importlib.util, os; from datetime import date
spec=importlib.util.spec_from_file_location("m","scripts/migrate.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.migrate()
from lab import classes as C, questions as Q; from lab.db import connect; from lab.streaks import current_streak
c=connect(); k=C.create_class(c,"Bio","m"); ben=C.enrol_student(c,k.id,"Ben"); cora=C.enrol_student(c,k.id,"Cora")
for t in ("2026-03-11T09:00:00","2026-03-12T09:00:00","2026-03-12T15:00:00"): Q.ask_question(c,k.id,ben.id,"q",t)
Q.hide_question(c,Q.ask_question(c,k.id,cora.id,"q","2026-03-12T10:00:00").id)
print("Ben",current_streak(c,ben.id,date(2026,3,12)),"(want 2)  Cora",current_streak(c,cora.id,date(2026,3,12)),"(want 0)")
