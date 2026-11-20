# Study Buddy (pipeline lab)

A small practice app for tracking students' questions in a class. Teachers create classes with
some course material and enrol students; students ask questions; a deterministic fake provider
answers each question from its own class's material. Data lives in SQLite (standard library
only). There is no web server and no network access.

## Layout

- `migrations/*.sql`: the schema, applied in order by `scripts/migrate.py`
- `src/lab/`: `classes`, `questions` (with pagination), `summary`, `ask` (answers), `providers/`
  (the fake provider), `jobs/` (a tiny job queue on the `jobs` table), `cli`
- `tests/`: each test runs against a fresh temporary database with the migrations applied

## Running it

```sh
uv sync --extra dev
export LAB_DB=./lab.db                  # optional; ./lab.db is the default
uv run python scripts/migrate.py        # safe to run more than once
uv run python -m lab.cli new-class Biology --material notes.txt
uv run python -m lab.cli summary 1
```

## Tests and checks

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

CI (`.github/workflows/ci.yml`) runs the same checks and applies the migrations twice on a fresh
database. The `risk-gate` workflow labels each pull request by the paths it changes, using
`.github/risk/rules.txt`.
