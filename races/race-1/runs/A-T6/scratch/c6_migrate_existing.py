"""C6: build a pre-0003 database with data, then run the real migrate script."""
import os, shutil, sqlite3, subprocess, tempfile
from pathlib import Path
db = os.environ["LAB_DB"]
if os.path.exists(db): os.remove(db)
root = Path.cwd()
tmp = Path(tempfile.mkdtemp(dir=os.path.dirname(db)))
for f in ("0001_init.sql", "0002_answers.sql"):
    shutil.copy(root / "migrations" / f, tmp / f)
import importlib.util
spec = importlib.util.spec_from_file_location("m", root / "scripts/migrate.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print("pre:", m.migrate(db, tmp))
c = sqlite3.connect(db)
c.execute("insert into classes values (1,'Bio','', '2026-01-01T00:00:00+00:00')")
for sid, name in [(1,'Ada'),(2,'Ben'),(3,'Cy'),(4,'Di')]:
    c.execute("insert into students values (?,1,?,'2026-01-01T00:00:00+00:00')", (sid, name))
qs = [(1,0,'2026-03-10T10:00:00+00:00'),(1,0,'2026-03-11T10:00:00+00:00'),   # Ada: 2 days
      (2,0,'2026-03-10T09:00:00+00:00'),(2,0,'2026-03-10T11:00:00+00:00'),   # Ben: 2 qs, 1 day
      (3,1,'2026-03-10T09:00:00+00:00')]                                     # Cy: hidden only; Di: none
for sid, h, t in qs:
    c.execute("insert into questions (class_id,student_id,text,hidden,asked_at) values (1,?,?,?,?)", (sid,'q',h,t))
c.commit(); c.close(); shutil.rmtree(tmp)
for i in (1, 2):
    r = subprocess.run(["uv","run","python","scripts/migrate.py"], capture_output=True, text=True)
    print(f"run {i}: rc={r.returncode}", (r.stdout + r.stderr).strip().splitlines()[-1])
c = sqlite3.connect(db)
print("streaks:", c.execute("select student_id,best from streaks order by 1").fetchall() if c.execute("select 1 from sqlite_master where name='streaks'").fetchone() else "NO TABLE")
print("migrations:", [r[0] for r in c.execute("select name from schema_migrations order by 1")])
