# Tickets

One folder per ticket, per codebase. Everything here and in `answers/` is frozen before stage 1.

## The eight tickets for a codebase

| Id | Kind | What it must catch |
|---|---|---|
| T1, T2, T3 | History replay | Real difficulty with a known right answer: a real bug-fix commit, replayed from the commit before it |
| T4 | Multi-file feature | A feature crossing at least 3 modules |
| T5 | Vague | One decision is left genuinely open; the owner has one fixed answer |
| T6 | Flawed | The request conflicts with a recorded decision or an existing test |
| T7 | Migration on data | A schema change that must keep existing rows intact |
| T8 | Review only | A branch with 3 planted bugs, one visible only when the code runs |

## Ticket package (what a run may see)

```
tickets/<codebase>/<T>/
  S1.md       the standard ticket: Problem / Why / Scope (In, Out) / Decisions / Done when / Notes
  S0.md       the rough capture as first filed, before triage          (not for T8)
  S2.md       S1 plus worked examples, explicit failure cases, a must-not-change list   (not for T8)
  S3.md       S2 plus one line naming the acceptance tests already in the branch        (not for T8)
  meta.json   see below
```

`meta.json`:

```json
{
  "id": "T1", "kind": "replay", "title": "short title",
  "repo": "Natenc12/gct-lab",
  "base_ref": "base/T1",          "s3_base_ref": "base/T1-s3",
  "db": "postgres",
  "deliverable": "pull_request",
  "spec_words": {"S0": 0, "S1": 0, "S2": 0, "S3": 0}
}
```

- `base_ref` is a branch in the practice repo that the run starts from. For a replay it is the commit
  before the real fix. `s3_base_ref` is the same commit plus the acceptance tests, in one extra commit.
- `deliverable` is `pull_request`, or `review_report` for T8 (the run writes `review.md` in its scratch
  folder; the grader also finds it under `repo/scratch/`).
- `spec_words` counts the words the owner would have to read and approve at each level.
- A ticket text never names the arm, the experiment, hidden tests, or the original fix. No code or
  hints copied from the original pull request. Every fact in it is true of the code at `base_ref`,
  except the planted flaw in T6, which `key.json` names.

## Answer package (never visible to a run)

```
answers/<codebase>/<T>/
  hidden/test_hidden_*.py   hidden tests, written against behaviour the ticket asks for
  reference.patch           a reference fix: `git diff` against base_ref that makes the hidden tests pass
  key.json                  see below
  replies.md                ticket-specific stand-in owner replies, in the reply-sheet format
  audit.md                  the auditor's verdict (written by the auditor, not the author)
```

`key.json`:

```json
{
  "hidden_test_cmd": "uv run pytest -q -m 'not live' tests/hidden",
  "unchanged_paths": ["paths that must be byte-identical to base_ref"],
  "scope_out_paths": ["paths the ticket puts out of scope"],
  "tests_may_change": ["existing tests a correct fix must update: a path or path::test_name"],
  "traps": [{"id": "applied-migration-edited", "check": "unchanged_paths", "paths": ["migrations/0001_init.sql"]}],
  "flaw": {"what": "T6 only: the conflict", "evidence": "file or decision record that shows it", "right_outcome": "raise it before building"},
  "open_decision": {"what": "T5 only", "owner_answer": "the one fixed answer", "hidden_tests_assume": "that answer"},
  "planted_bugs": [{"id": 1, "where": "file:line", "what": "", "visible": "diff | edge case | only when run"}],
  "not_bugs": ["T8: things a reviewer may flag that are not defects"],
  "other_real_defects": ["T8: real defects on the review branch that were not planted"]
}
```

`tests_may_change` is optional. Editing or removing an existing test is a trap unless an entry here matches
its file path or `path::test_name` (globs allowed, as in the other path lists). A replay whose real fix
changed an existing test must list that test, or the grader's dry run fails the reference fix.

`other_real_defects` is optional (T8 only): short descriptions of real defects on the review branch that
the author did not plant. The review judge never counts a blocking finding that matches one as a false
alarm, and a run that misses them loses nothing.

Rules for hidden tests: each fails on `base_ref`, passes with `reference.patch`, checks only behaviour
the ticket text asks for (not too wide), and would pass for a different correct fix (not too narrow).
They need no network and no paid API.

`replies.md` uses the harness sheet format (`## <id>`, `When:`, `Reply:`). Ids are prefixed with the
ticket, for example `T5-open-decision`. The common replies live in `answers/reply-sheet-common.md`.

## Optional extras in an answer package

Not required by the format above; used by the gct packages and the tools in `tickets/tools/`.

| File | What it is |
|---|---|
| `naive.patch`, `naive-*.patch` | A careless but competent fix. `verify_ticket.py` shows each fails at least one hidden test while the existing tests pass. `naive-s3.patch`, if present, is the one used against `s3_base_ref` (it must pass the acceptance tests and still fail a hidden test) |
| `acceptance/` | The files `base/<T>-s3` adds, at their repo paths; `make_base_branches.py` commits them |
| `feature.patch` | T8 only: the change under review, which `make_base_branches.py` commits on top of the review base |
| `verify.json` | Output of `tickets/tools/verify_ticket.py` |

Every gct starting branch is free of agent-instruction files (`CLAUDE.md`, `AGENTS.md`, `.claude/`):
where the source commit had them, `make_base_branches.py` adds one commit on top that deletes them, so
a replay's `base_ref` is the commit before the fix plus that one commit. `meta.json` records the
resulting `base_commit`.

`meta.json` and `key.json` for a review ticket also carry `review_base_commit`. A trap's `check` may
be `hidden_tests_pass` (the hidden tests themselves fail when the naive version was shipped) besides
`unchanged_paths` and `scope_out_paths`. Runs on gct need `UV_PYTHON=3.10`: the app does not compile
on Python 3.13+.

## Stage 2 tickets (T9 to T12)

| Id | Kind | What it must catch |
|---|---|---|
| T9, T10 | Long, many-file | Drift: rules stated at the top of the ticket that only matter late in the work (`meta.json` has `"long": true`; `key.json`'s `long_ticket` maps each rule to the hidden tests that check it) |
| T11, T12 | Flawed | Building the wrong thing as asked, when the flaw is not a decision record: a false premise about the code (T11), a rule pinned only by code and tests (T12) |

For a flawed ticket whose S3 acceptance tests are written to hold for both the request as written and
the owner's amended request, those tests may already pass on the starting branch; `key.json` then says
`"acceptance_may_pass_on_base": true` and `verify_ticket.py` records the run instead of requiring a
failure. Their starting branches are tagged `stage-2-candidate/base/<T>` until the stage 2 freeze.

T9 is not for use at S0: its rough capture names none of the keys, routes or reply shapes the hidden
tests assert, so no S0 run can pass (`meta.json`: `not_for_spec_levels`).

## sqlglot tickets (stage 4, T1 to T8)

The second codebase for the model comparison: [tobymao/sqlglot](https://github.com/tobymao/sqlglot), a
pure-Python SQL parser and translator, in the private practice repo `Natenc12/sqlglot-lab`. Standard
level (S1) only: no S0, S2 or S3, so no `base/<T>-s3` branches and no acceptance tests
(`meta.json`: `"spec_levels": ["S1"]`).

| Id | Kind | What it is |
|---|---|---|
| T1 | Replay | Parser: a column named `top` read as a row limit (Snowflake, Oracle) |
| T2 | Replay | Tokenizer: Snowflake stage paths cut off at `--`, `//`, `/*` |
| T3 | Replay | Optimizer: unnesting a correlated `IN` changes results outside plain filters |
| T4 | Replay | Generator: Spark `EXISTS(array, lambda)` loses its lambda in other dialects |
| T5 | Replay | Parser and generator: SQLite `UPDATE OR REPLACE` |
| T6 | Feature | Cosine similarity as its own function across expressions, parsers, generators and typing |
| T7 | Vague | The optimizer tidies up `COALESCE`; what to do after a non-NULL constant is left open |
| T8 | Flawed | Asks to make `python-dateutil` a required dependency; sqlglot's written rules say no dependencies |

- **Practice copy.** `main` is upstream `089891f` (2026-11-20) plus one setup commit. Every starting
  branch is its source commit plus the same kind of setup commit, made by `make_base_branches.py`
  (`PREP`): `CLAUDE.md` and upstream `.github/workflows` removed, the integration-test submodule
  dropped, the lines asking agents to tag commits with their model removed from `AGENTS.md` and
  `CONTRIBUTING.md` (`AGENTS.md` stays as an ordinary project document), and a small workflow of our
  own (`tickets/tools/practice/sqlglot/tests.yml`) that installs and runs the tests on pull requests.
  T6 to T8 start from `main`; replays from the parent of the real fix. Starting branches are tagged
  `stage-4-candidate/base/<T>` until the freeze.
- **Replays** come from fixes merged in November 2026 whose commits carry no `[CODEX]` or `[CLAUDE]`
  tag. `reference.patch` is the fix's whole diff, tests included. Hidden tests are the fix's own
  tests, rewritten where they named the fix's internals (private argument names, token types) or
  pinned one spelling of an answer the ticket leaves open (DuckDB output is run on DuckDB instead).
- **Commands.** The grader config is `grader/codebases/sqlglot.json`. The virtual environment lives
  in the repo folder (`.venv`, Python 3.13); tests run with pytest (added at install, not in the
  project's dev extras) and `-p no:subtests`, with `.venv/bin` first on `PATH` and
  `SKIP_INTEGRATION=1`. Hidden tests go to `tests/hidden/`. `SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0` is set
  because sqlglot reads its version from git tags, and the `stage-4-candidate/...` tags are not
  versions: without it, installing at a tagged checkout fails. `verify_ticket.py`, `make_base_branches.py`
  and `check_packages.py` take `sqlglot` as the codebase; the practice clone defaults to
  `~/repos/sqlglot-lab`.
- **Lint.** `answers/sqlglot/ruff.toml` sets 100-character lines so hidden tests pass both this repo's
  lint and the practice repo's own.

## Hono tickets (stage 4, model comparison)

Practice copy `Natenc12/hono-lab` (private; local clone `~/repos/hono-lab`): upstream `honojs/hono` with its
history, `main` = upstream `9075031` (v4.13.21, 2026-11-23) plus one setup commit made by
`make_base_branches.py hono` (upstream `.github/` removed, the test-only workflow in
`tickets/tools/practice/hono/test.yml` added; no agent-instruction files existed). Every starting
branch is a source commit plus that same setup commit. Starting branches are tagged
`stage-4-candidate/base/<T>` until the freeze.

| Id | Kind | What it must catch |
|---|---|---|
| T1 to T5 | History replay | Real fixes merged after 1 July 2026, from the issue text with fix hints removed (router, middleware, Bun adapter, JSX, client) |
| T6 | Feature | Request id reaching the logger and the `Server-Timing` header (three middlewares) |
| T7 | Vague | Wildcard origins in `cors()` and `csrf()`; what `*` matches is left open |
| T8 | Wrong request | `serveStatic` answering POST, which code and tests rule out; the owner's real need is an opt-in redirect |

Differences from the gct format:

- **Standard level only.** Each ticket has `S1.md`; `meta.json` says `"spec_levels": ["S1"]` and has no
  `s3_base_ref`. Replays record `source_fix` in `meta.json` and `source` (fix, pull request, issue,
  author) in `key.json`.
- **Hidden tests** are vitest files (`answers/hono/<T>/hidden/*.test.ts(x)`), copied into `src/hidden/`
  and run with `pnpm exec vp test --run src/hidden`. They import with relative paths (`../hono`). The
  main suite must run before they are copied in, because `src/hidden` is inside the type check's
  include. Replays use the upstream fix's own tests, minus cases that already pass on the base.
- **Traps** use `unchanged_paths`, `scope_out_paths` and `hidden_tests_pass` only (`ast_unchanged` is
  Python-specific).
- **Guard tests.** A wrong-request ticket may have one hidden test that passes on the base because it
  checks that the request as written was not built (T8: a POST is not served the file by default). The
  key names it in `hidden_tests_may_pass_on_base`, its `built-as-asked` trap watches only it, and
  `verify_ticket_hono.py` checks that each `built-as-asked*.patch` fails it.
- **An existing test** is an `it(...)` / `test(...)` block in a `*.test.ts(x)` file, named
  `path::describe > ... > case` as the grader reads it. `src/router/common.case.test.ts` holds cases
  every router runs, and each router's test file passes `runTest()` a skip list: that call is data,
  not a test, so T1 guards it with a hidden test instead. `check_packages.py hono --lab ~/repos/hono-lab`
  checks `tests_may_change` the same way.
- **Tools.** `verify_ticket.py hono <T>` hands over to `verify_ticket_hono.py` (offline install from
  pnpm's store, build, type check, vitest's JSON report); no database. Grader settings are in
  `grader/codebases/hono.json`.
- **One test file is left out of grading.** `runtime-tests/node/index.test.ts` (the Node adapter's server
  tests, the only file in vitest's `node` project) is left out with `--project=!node`: its "Should call
  onAbort" tests use 10 ms sleeps and failed about 9 times in about 40 full-suite runs on 2026-11-23,
  mostly while other suites ran at once. The graded command also raises vitest's 5 s time limit to 30 s
  (`--testTimeout=30000`): `build/jsx-types.test.ts` spawns `tsc` and overran 5 s under the same load.
  No ticket touches the Node adapter, the streaming helpers or the build checks.
