import os, importlib.util
from datetime import date
from pathlib import Path
from lab import classes, questions
from lab.db import connect
from lab.streaks import current_streak, best_streak, record_streak
spec = importlib.util.spec_from_file_location("m", Path("scripts/migrate.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.migrate()
c = connect(); k = classes.create_class(c, "Bio", "x")
n = iter(range(1000))
def student(): return classes.enrol_student(c, k.id, f"s{next(n)}")
def ask(s, t, hide=False):
    q = questions.ask_question(c, k.id, s.id, "q", t)
    if hide: questions.hide_question(c, q.id)
T = date(2026, 3, 12)
s = student(); [ask(s, f"2026-03-{d}T10:00:00+00:00") for d in (10, 11, 12)]
print("C1 3 days ending today (expect 3):", current_streak(c, s.id, T))
s = student(); [ask(s, f"2026-03-{d}T10:00:00+00:00") for d in (10, 12)]
print("C1 gap yesterday (expect 1):", current_streak(c, s.id, T))
s = student(); [ask(s, f"2026-03-{d}T10:00:00+00:00") for d in (10, 11)]
print("C2 ending yesterday (expect 2):", current_streak(c, s.id, T))
s = student(); ask(s, "2026-03-10T10:00:00+00:00")
print("C2 ending day before (expect 0):", current_streak(c, s.id, T))
s = student(); [ask(s, f"2026-03-{d}T{h}:00:00+00:00") for d in (10, 11, 12) for h in ("09", "15")]
print("C3 two questions/day on 3 days (expect 3):", current_streak(c, s.id, T))
s = student(); ask(s, "2026-03-11T10:00:00+00:00"); ask(s, "2026-03-12T09:00:00+00:00"); ask(s, "2026-03-12T15:00:00+00:00")
print("C3 yesterday + 2 today (expect 2):", current_streak(c, s.id, T))
s = student(); ask(s, "2026-03-12T10:00:00+00:00", hide=True)
print("C3 hidden-only today (expect 0):", current_streak(c, s.id, T))
s = student(); ask(s, "2026-03-10T10:00:00+00:00"); ask(s, "2026-03-11T10:00:00+00:00", hide=True); ask(s, "2026-03-12T10:00:00+00:00")
print("C3 hidden-only yesterday breaks it (expect 1):", current_streak(c, s.id, T))
s = student()
print("C4 best no row (expect 0):", best_streak(c, s.id))
[ask(s, f"2026-03-{d}T10:00:00+00:00") for d in (10, 11, 12)]
print("C4 record (expect 3):", record_streak(c, s.id, T), "later (expect 3):", record_streak(c, s.id, date(2026, 3, 20)), best_streak(c, s.id))
for fn in (current_streak, best_streak, record_streak):
    try: fn(c, 999); print("C5", fn.__name__, "NO ERROR")
    except LookupError as e: print("C5", fn.__name__, "LookupError")
s = student(); ask(s, "2026-03-11T22:00:00-05:00")   # = 2026-03-12T03:00Z
print("C7 offset timestamp, UTC date is today (expect 1):", current_streak(c, s.id, T))
