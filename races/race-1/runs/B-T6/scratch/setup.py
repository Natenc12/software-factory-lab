import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("m", "scripts/migrate.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m.migrate(None, Path(sys.argv[1])))
from lab import classes, questions; from lab.db import connect
c = connect(); k = classes.create_class(c, "Bio", "m")
a = classes.enrol_student(c, k.id, "Ada"); classes.enrol_student(c, k.id, "Ben")
for d in ("09", "11", "12"): questions.ask_question(c, k.id, a.id, "q", f"2026-03-{d}T10:00:00+00:00")
