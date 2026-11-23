# System map

A study tutor. Students upload their course materials to a class and ask questions; every answer is
cited to the file and page or slide it came from, or the app says the materials do not cover it.
The Python core is a library; the HTTP API, the worker process, the scripts and the evaluation are
thin callers of it.

## The parts

| Folder | What it holds |
| --- | --- |
| `src/` | The core package. Paths in this table and below are relative to it. `api/`: the FastAPI adapter (routers for classes, files, ask and health; `schemas.py`, `errors.py`, `limits.py`), meant to hold no business logic. `classes.py`, `files.py`, `staging.py`: classes, file status, and where uploaded bytes land on disk. `jobs/`: the job queue (`queue.py` writes job rows) and the worker (`worker.py` decides job and file state). `ingest/`: parse, chunk, index, and `pipeline.py`, which joins them. `retriever/`, `grounder/`, and `ask.py`, the read path's entry point. `providers/`: the embedding and generation interfaces, a paid provider and an offline stand-in, picked in `providers/active.py`. `config.py`, `db.py`, `ids.py`, `eval/` |
| `web/` | The React and TypeScript client (Vite), which talks to the API |
| `scripts/` | Thin callers: `migrate.py` applies the schema, `worker.py` runs the worker process, and smoke scripts drive the loop end to end |
| `migrations/` | The schema as numbered SQL files, applied in order by `scripts/migrate.py` |
| `tests/` | pytest suite, laid out like the code. CI applies the migrations twice, then runs every test not marked `live` (paid model calls) against Postgres |
| `eval/`, `data/` | The evaluation questions and findings; sample course material |
| `design/` | The design documents and the decision records |

## How a request flows

- **Ingest (write):** `POST /files` stages the bytes on disk, records the file as `queued` and enqueues
  a job, then returns. The worker process claims the job, then parses (page and slide numbers are
  recorded here), chunks, embeds and indexes the file, and marks it `ready` or `failed`.
  `GET /files/:id` reports that status.
- **Ask (read):** `POST /ask` goes to the retriever (embed the question, find the closest chunks for
  this owner within one class, each with its similarity), then to the grounder (number the chunks,
  generate, turn the numbers back into citations), and returns a cited answer, a partly supported
  answer, or a refusal.
- **Classes:** `POST /classes` creates the class that files and questions belong to.

## Where rules and decisions are recorded

- **`design/decisions/`**: numbered decision records, one decision each, with its reasons. A decision
  changes only through a later record; its status line says "amends NNNN" or "superseded by NNNN",
  and the later record wins. By area:
  - Scope and approach: 0001, 0002, 0003, 0004, 0006, 0022, 0026
  - Models and embeddings: 0005, 0007, 0013, 0018
  - Uploads, jobs and the worker: 0010, 0011, 0019, 0020, 0025, 0027, 0028, 0029, 0030, 0031
  - Asking (retriever and grounder): 0008, 0009, 0014, 0015, 0016, 0017, 0024
  - Evaluation: 0021, 0023
  - Client: 0012, 0032
- **`design/architecture.md`** (the shape and the rules that hold across it), **`design/components/`**
  (specs for the API, retriever, grounder and ingestion worker), **`design/data-model.md`** (tables
  and their rules) and **`design/requirements.md`** (numbered requirements). `design/vision.md` is
  the first proposal; where it disagrees with a later document, the later one wins.
- **The code itself:** most modules open with a docstring naming the decision records and rules they
  carry out. Tests pin current behaviour, and migrations hold the schema.

## Before you plan a change

Find the decision records, component spec and tests that touch the area you are changing, and read
them first.
