"""Reviewer's own checks, written from the contract before reading the diff."""
import importlib.util, os, sqlite3, sys, tempfile, traceback
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path("/Users/nathan/repos/lab-worktrees/B-T6")
spec = importlib.util.spec_from_file_location("migrate", ROOT / "scripts/migrate.py")
mig = importlib.util.module_from_spec(spec); spec.loader.exec_module(mig)
from lab import classes, questions
from lab.db import connect
import lab.streaks as S

TODAY = date(2026, 3, 12)
results = []
def check(name, fn):
    try:
        got = fn(); results.append((name, "OK" if got is True else f"FAIL got={got!r}"))
    except Exception as e:
        results.append((name, f"ERROR {type(e).__name__}: {e}"))

def fresh(dirs=None):
    d = tempfile.mkdtemp(dir="/Users/nathan/repos/pipeline-bench/runs/B-T6/scratch")
    p = os.path.join(d, "t.db")
    mig.migrate(p, dirs) if dirs else mig.migrate(p)
    c = connect(p)
    k = classes.create_class(c, "Bio", "m")
    return c, k, p

def stu(c, k, name):
    return classes.enrol_student(c, k.id, name)

def ask(c, k, s, ts, hide=False):
    q = questions.ask_question(c, k.id, s.id, "q", asked_at=ts)
    if hide: questions.hide_question(c, q.id)
    return q

def e1():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    for d in ("10","11","12"): ask(c,k,a,f"2026-03-{d}T10:00:00+00:00")
    return S.current_streak(c,a.id,today=TODAY)==3 or S.current_streak(c,a.id,today=TODAY)
check("E1 Ada 10,11,12 -> 3", e1)
def e2a():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    for d in ("10","11"): ask(c,k,a,f"2026-03-{d}T10:00:00+00:00")
    r=S.current_streak(c,a.id,today=TODAY); return r==2 or r
check("E2a Ada 10,11 nothing today -> 2", e2a)
def e2b():
    c,k,_=fresh(); a=stu(c,k,"Ada"); ask(c,k,a,"2026-03-09T10:00:00+00:00")
    r=S.current_streak(c,a.id,today=TODAY); return r==0 or r
check("E2b Ada only Mar 9 -> 0", e2b)
def e3():
    c,k,_=fresh(); b=stu(c,k,"Ben")
    for ts in ("2026-03-11T09:00:00+00:00","2026-03-12T09:00:00+00:00","2026-03-12T15:00:00+00:00"): ask(c,k,b,ts)
    r=S.current_streak(c,b.id,today=TODAY); return r==2 or r
check("E3 Ben two on Mar12 -> 2", e3)
def e4():
    c,k,_=fresh(); x=stu(c,k,"Cora"); ask(c,k,x,"2026-03-12T10:00:00+00:00",hide=True)
    r=S.current_streak(c,x.id,today=TODAY); return r==0 or r
check("E4 Cora hidden -> 0", e4)
def e5():
    c,k,_=fresh(); x=stu(c,k,"Dan")
    r=(S.current_streak(c,x.id,today=TODAY), S.best_streak(c,x.id)); return r==(0,0) or r
check("E5 no questions -> 0,0", e5)
def e6():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    for d in ("10","11","12"): ask(c,k,a,f"2026-03-{d}T10:00:00+00:00")
    r=(S.record_streak(c,a.id,today=TODAY), S.record_streak(c,a.id,today=date(2026,3,20)), S.best_streak(c,a.id))
    return r==(3,3,3) or r
check("E6 record 3 then still 3", e6)

def snapshot(c):
    tabs=[r[0] for r in c.execute("select name from sqlite_master where type='table' and name not in ('schema_migrations','streaks')")]
    return {t: [tuple(r) for r in c.execute(f"select * from {t} order by rowid")] for t in tabs}
def e7():
    d = tempfile.mkdtemp(dir="/Users/nathan/repos/pipeline-bench/runs/B-T6/scratch")
    old = Path(d)/"old"; old.mkdir()
    for n in ("0001_init.sql","0002_answers.sql"): (old/n).write_text((ROOT/"migrations"/n).read_text())
    p=os.path.join(d,"t.db")
    first=mig.migrate(p, old)
    c=connect(p); k=classes.create_class(c,"Bio","m"); a=stu(c,k,"Ada"); b=stu(c,k,"Ben"); x=stu(c,k,"Cora")
    for ts in ("2026-03-09T10:00:00+00:00","2026-03-11T10:00:00+00:00","2026-03-12T10:00:00+00:00"): ask(c,k,a,ts)
    ask(c,k,x,"2026-03-12T10:00:00+00:00",hide=True)  # hidden-only student: no row expected
    c.execute("insert into answers (question_id, body, provider, created_at) values (1,'b','fake','2026-03-09')")
    c.execute("insert into jobs (kind, created_at, updated_at) values ('k','t','t')"); c.commit()
    before=snapshot(c); c.close()
    second=mig.migrate(p); third=mig.migrate(p)
    c=connect(p); after=snapshot(c)
    rows=[tuple(r) for r in c.execute("select student_id,best from streaks")]
    cols=[r[1] for r in c.execute("pragma table_info(streaks)")]
    pk=[r[1] for r in c.execute("pragma table_info(streaks)") if r[5]]
    upd=[r[0] for r in c.execute("select updated_at from streaks")]
    out=dict(first=first,second=second,third=third,rows=rows,cols=cols,pk=pk,unchanged=before==after,updated_at=upd)
    ok = first==["0001_init.sql","0002_answers.sql"] and second==["0003_streaks.sql"] and third==[] and rows==[(a.id,1)] and before==after and set(cols)>={"student_id","best","updated_at"} and pk==["student_id"]
    return ok or out
check("E7 migration backfill/idempotent/rows survive", e7)

# Decisions / edges
def unknown():
    c,k,_=fresh()
    try: S.current_streak(c,999,today=TODAY)
    except LookupError: return True
    return "no LookupError"
check("D current_streak unknown student -> LookupError", unknown)
def unknown_rec():
    c,k,_=fresh()
    try: r=S.record_streak(c,999,today=TODAY)
    except LookupError: return True
    except Exception as e: return f"{type(e).__name__}: {e}"
    return f"returned {r}"
check("edge record_streak unknown student -> LookupError", unknown_rec)
def utc_offset():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    # 2026-03-11T22:00-05:00 is Mar 12 03:00 UTC; Mar 11 10:00 UTC also asked -> 2
    ask(c,k,a,"2026-03-11T10:00:00+00:00"); ask(c,k,a,"2026-03-11T22:00:00-05:00")
    r=S.current_streak(c,a.id,today=TODAY); return r==2 or r
check("D UTC day of asked_at with -05:00 offset", utc_offset)
def utc_offset2():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    # 2026-03-12T01:00+05:00 is Mar 11 20:00 UTC -> only Mar 11 -> streak from yesterday = 1
    ask(c,k,a,"2026-03-12T01:00:00+05:00")
    r=S.current_streak(c,a.id,today=TODAY); return r==1 or r
check("D UTC day of asked_at with +05:00 offset", utc_offset2)
def hidden_gap():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    ask(c,k,a,"2026-03-10T10:00:00+00:00"); ask(c,k,a,"2026-03-11T10:00:00+00:00",hide=True); ask(c,k,a,"2026-03-12T10:00:00+00:00")
    r=S.current_streak(c,a.id,today=TODAY); return r==1 or r
check("D hidden day breaks streak", hidden_gap)
def mixed_day():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    ask(c,k,a,"2026-03-11T10:00:00+00:00"); ask(c,k,a,"2026-03-12T08:00:00+00:00",hide=True); ask(c,k,a,"2026-03-12T10:00:00+00:00")
    r=S.current_streak(c,a.id,today=TODAY); return r==2 or r
check("D day with hidden+visible counts", mixed_day)
def future():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    ask(c,k,a,"2026-03-11T10:00:00+00:00"); ask(c,k,a,"2026-03-12T10:00:00+00:00"); ask(c,k,a,"2026-03-14T10:00:00+00:00")
    r=S.current_streak(c,a.id,today=TODAY); return r==2 or r
check("edge question after 'today' ignored", future)
def default_today():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    ask(c,k,a,None)  # now()
    r=S.current_streak(c,a.id); return r==1 or r
check("D today defaults to UTC date", default_today)
def first_record_zero():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    r=S.record_streak(c,a.id,today=TODAY); n=c.execute("select count(*) from streaks where student_id=?",(a.id,)).fetchone()[0]
    return (r,n)==(0,1) or (r,n)
check("D first record_streak creates row (current 0)", first_record_zero)
def lower_keeps():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    for d in ("10","11","12"): ask(c,k,a,f"2026-03-{d}T10:00:00+00:00")
    S.record_streak(c,a.id,today=TODAY)
    ask(c,k,a,"2026-03-20T10:00:00+00:00")
    r=(S.record_streak(c,a.id,today=date(2026,3,20)), S.best_streak(c,a.id)); return r==(3,3) or r
check("D lower current keeps best", lower_keeps)
def backfilled_then_record():
    # after migration Ada has best=1; her current streak 2 should raise it
    c,k,_=fresh(); a=stu(c,k,"Ada")
    c.execute("insert into streaks (student_id,best,updated_at) values (?,1,'2026-01-01T00:00:00+00:00')",(a.id,)); c.commit()
    ask(c,k,a,"2026-03-11T10:00:00+00:00"); ask(c,k,a,"2026-03-12T10:00:00+00:00")
    r=S.record_streak(c,a.id,today=TODAY); u=c.execute("select updated_at from streaks where student_id=?",(a.id,)).fetchone()[0]
    return (r==2 and u!='2026-01-01T00:00:00+00:00') or (r,u)
check("D record raises backfilled best and updates updated_at", backfilled_then_record)
def persisted():
    c,k,p=fresh(); a=stu(c,k,"Ada"); ask(c,k,a,"2026-03-12T10:00:00+00:00")
    S.record_streak(c,a.id,today=TODAY); c.close()
    c2=connect(p); r=S.best_streak(c2,a.id); return r==1 or r
check("edge record_streak is committed", persisted)
def other_student():
    c,k,_=fresh(); a=stu(c,k,"Ada"); b=stu(c,k,"Ben")
    for d in ("10","11","12"): ask(c,k,b,f"2026-03-{d}T10:00:00+00:00")
    r=S.current_streak(c,a.id,today=TODAY); return r==0 or r
check("edge other student's questions don't count", other_student)
def long_streak():
    c,k,_=fresh(); a=stu(c,k,"Ada")
    from datetime import timedelta
    for i in range(400): ask(c,k,a,(datetime(2026,3,12,12,tzinfo=timezone.utc)-timedelta(days=i)).isoformat())
    r=S.current_streak(c,a.id,today=TODAY); return r==400 or r
check("edge 400-day streak across year boundary", long_streak)
def str_today():
    c,k,_=fresh(); a=stu(c,k,"Ada"); ask(c,k,a,"2026-03-12T10:00:00+00:00")
    try: r=S.current_streak(c,a.id,today="2026-03-12")
    except Exception as e: return f"{type(e).__name__}: {e}"
    return r==1 or r
check("info today as ISO string", str_today)

for n,r in results: print(f"{r[:4]:5} {n}  {'' if r=='OK' else r}")
