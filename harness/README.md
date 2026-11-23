# Harness

Starts each run as its own headless Claude Code session, in its own sandbox, and records what it cost.
Python 3.11+, standard library only; needs `claude`, `git`, `gh`, and `psql` for Postgres runs.

| Command | What it does |
| --- | --- |
| `python3 -m harness.stage <plan.json>` | Runs a whole stage, 4 at a time, inside a token budget. Safe to re-invoke |
| `python3 -m harness.run <run-id> --stage ... --ticket ... --repo ... --base ... --model ... --ceiling ...` | Starts or continues one run (`--help` lists every option) |
| `python3 -m harness.scan <run folder>` | Leak scan of a run's transcript; writes `scan.json` |
| `python3 -m harness.sandbox down <run folder> [--all]` | Drops the run's database, removes its files |

`SMOKE.md` has the two smoke-run commands. `TRIALS.md` records the real calls that confirmed the CLI
flags, the clean room and resume.

## How a run works

1. **Sandbox** at `~/factory-runs/<stage>/<run-id>/` (`sandbox.py`): `repo/` holds only the base ref's
   history on branch `<run-id>/work`, with no remote; `scratch/`, `TICKET.md`, `arm/`, and an SQLite
   file (`db/lab.db`, as `LAB_DB` and `DATABASE_URL`) or a Postgres database `run_<run_id>` with
   `vector`, reached through its Unix socket (`DATABASE_URL`, `PGHOST`). Records live in `harness/`.
   The run's controls (settings, guard hook, `lab`) live outside the run folder, in
   `~/factory-runs/<stage>/.control/<run-id>/`. The session can neither read nor write either one.
2. **Clean room** (`run.py`): `--setting-sources ""` (no user, project or local settings, so no user
   skills, hooks, plugins or output style), `--disable-slash-commands`, `--strict-mcp-config`,
   `--tools` with a fixed list, `--permission-mode dontAsk`, auto-memory off, and a minimal
   environment. The arm's instruction files are appended to the system prompt; an arm's
   `agents/*.md` become `--agents`. An arm with a `skills/` folder (opt-in) gets those skills as a plugin
   from the control folder (`--plugin-dir`), the `Skill` tool, and settings that keep Claude Code's own
   skills out (`disableBundledSkills`, `skillOverrides`, and `Skill(work:<name>)` allow rules only);
   `run.json` lists the skills it called in `skills_used`. Without `skills/`, nothing changes.
   An agent file may name its own hooks with `hooks: hooks/<role>.json`
   (Claude Code's hook format); `{python}`, `{arm}` and `{run}` in it are filled in, and the hooks run
   from a copy of the arm in the control folder, so the session cannot change them.
3. **Fence, first layer: the OS sandbox** in the run's `settings.json`. Every Bash command, and every
   program it starts, may reach only PyPI (`pypi.org`, `files.pythonhosted.org`, plus any
   `--allow-domain`) and the Postgres socket; it may write only in the run folder, its temp folder and
   the shared uv cache; it may not read `~/.config/gh`, `~/.ssh`, `~/.claude`, `~/repos`, this repo or
   other runs. `allowUnsandboxedCommands: false` removes the escape hatch and `failIfUnavailable`
   stops the run if the sandbox can't start. The one exception is `lab` (`lab.py`), which runs outside
   the sandbox only when a call is `lab ...` and nothing else: ticket, open or update this run's one
   pull request, and its checks. `lab` never merges, labels or comments.
   **Second layer:** deny rules (absolute paths written `//...`; `Edit(...)` also covers Write) and a
   PreToolUse hook (`guard.py`) that blocks web tools, `gh`, `curl`, git's remote commands, and paths
   outside the sandbox. They also cover the Read, Edit and Write tools, which the OS sandbox does not.
4. **Stop and reply** (`owner.py`): a turn ending in a `STOP:` line is saved with its page, stripped of
   the arm's name and run id, and given to a reply judge (`claude -p`, no tools) with the reply sheet.
   The judge's reply id picks the exact text sent back with `--resume`. Every reply goes to
   `owner-log.jsonl`. At most 6 stops by default.
5. **Ceiling and records** (`stream.py`): usage is read live from the stream; the run is stopped when
   counted tokens (input + output + cache write) pass its ceiling. `run.json` holds the status
   (`finished`, `ceiling_hit`, `harness_fault`, `plan_limit`), the four token counts, CLI-reported cost,
   wall time, turns, stops, session id, branch, PR number and both commits. It also holds `by_model` (counted
   tokens and list-price cost per model, the lead's and any subagent's; the ceiling counts them all
   together), `workers_started` and `workers` (each subagent the lead started, with its type and a
   one-line gist of its task), and `skills_used`.

## Codebases in other languages

**Settable today, per codebase or per run.** In `grader/codebases/<name>.json`:

- `run_allow_domains`: hosts the run's sandbox may reach on top of `pypi.org` and `files.pythonhosted.org`.
- `run_allow_write`: folders outside the run the sandbox may write, such as a toolchain's shared cache.
- `run_setup`: shell commands the harness runs once in the checkout before the session starts, outside
  the sandbox and with network (installing dependencies). Output goes to `harness/setup.log` and the
  exit codes to `run.json` (`setup`); a failing command makes the run a `harness_fault` before any
  model call. `{run}` in a command becomes the run's folder.
- `run_env`: environment variables. `{run}` in a value becomes the run's folder, for example
  `"GOMODCACHE": "{run}/scratch/gomod"` to keep a cache inside the run.

`grader.make_plan` copies these into every run as `allow_domain`, `allow_write`, `env` and `setup`. A plan can
also set them per run; `harness.stage` passes them to `harness.run` as `--allow-domain`,
`--allow-write` and `--env`. `tests/test_codebase_sandbox.py` checks the path from config to the run's
settings. A write folder may not be home, `/`, this repo, `~/repos`, `~/.claude`, the gh login, other
runs, or a parent of any of these.

**Hono and sqlglot (checked in the run sandbox, 2026-11-23; `harness/TRIALS.md` trials 12–17).**
Installing before the session keeps the sandbox at its default hosts: the session needs no package
registry, so no package downloads or install scripts run where the agent works.

| Key | Hono (`grader/codebases/hono.json`) | sqlglot (`grader/codebases/sqlglot.json`) |
| --- | --- | --- |
| `db` | `"none"` | `"none"` |
| `run_setup` | `["pnpm install --frozen-lockfile"]` | `["uv venv -q -p 3.13 .venv && uv pip install -q -p .venv -e \".[dev]\"", <the line below>]` |
| `run_env` | `{"CI": "1", "PNPM_HOME": "{run}/scratch/pnpm-home", "XDG_CACHE_HOME": "{run}/scratch/xdg-cache", "XDG_CONFIG_HOME": "{run}/scratch/xdg-config", "XDG_DATA_HOME": "{run}/scratch/xdg-data", "XDG_STATE_HOME": "{run}/scratch/xdg-state"}` | `{"SKIP_INTEGRATION": "1"}` |
| `run_allow_domains` | none | none |
| `run_allow_write` | none | none |

- **Hono:** `PNPM_HOME` inside the run holds the pinned pnpm (12.6.0, fetched at setup) and the package
  store. pnpm hard-links `node_modules` to its store, so a shared store would let one run's edits reach
  another's. In the session, `pnpm run build` and `pnpm test` pass with no network (147 files, 6,147
  tests, 108 skipped); pnpm's calls to `registry.npmjs.org` are refused and do no harm.
- **sqlglot:** macOS's sandbox refuses the one system query Python's process pool makes at start
  (`os.sysconf("SC_SEM_NSEMS_MAX")`), so `tests/test_optimizer.py` fails at class setup. The second setup
  line writes a one-line `.pth` file into the run's own `.venv` that answers that query with `-1`
  (Python's "no limit"):
  `echo "import os; _f = os.sysconf; os.sysconf = lambda n, _f=_f: -1 if n == \"SC_SEM_NSEMS_MAX\" else _f(n)" > "$(.venv/bin/python -c "import sysconfig; print(sysconfig.get_path(\"purelib\"))")/zz_sandbox_sem_limit.pth"`.
  With it the suite passes in the session (1,779 tests, 60 skipped). Grading runs outside the sandbox
  and doesn't need it. One test runs a bare `python`, so it needs `.venv/bin` on `PATH`
  (`PATH="$PWD/.venv/bin:$PATH" python -m unittest`).

**What a non-Python codebase would need** (from the docs and the sandbox rules, not tried):

| Need | TypeScript (npm or pnpm) | Go | Rust |
| --- | --- | --- | --- |
| Hosts | `registry.npmjs.org` | `proxy.golang.org`, `sum.golang.org` | `index.crates.io`, `static.crates.io`, `crates.io` |
| Cache it writes outside the run | `~/.npm` (or `npm_config_cache={run}/scratch/npm`); the pnpm store | `GOMODCACHE` (`~/go/pkg/mod`) and `GOCACHE` (`~/Library/Caches/go-build` on macOS) | `~/.cargo/registry` and `~/.cargo/git` (or `CARGO_HOME={run}/scratch/cargo`) |
| Toolchain | `node` on the harness's `PATH` | `go` on `PATH`; `GOTOOLCHAIN=local` so it never downloads a newer Go | `cargo` and `rustc` on `PATH` (`~/.cargo/bin`); toolchain already installed, since rustup downloads from `static.rust-lang.org` |

The same for every language:

- **The toolchain must be on the harness's own `PATH`.** A run's environment starts from it. Don't set
  `PATH` with `env`: that replaces the run's own `lab` folder at the front.
- **Nothing hosted on GitHub can be reached.** Dependencies fetched from git (npm git URLs, cargo `git =`
  dependencies, Go modules not on the proxy) and install scripts that download release binaries
  (esbuild, Playwright, prebuilt native modules) will fail. Vendor them, or pick a codebase without them.
- **Postgres or SQLite only.** The run database is one of those two. Another service would need its own
  socket in `allowUnixSockets`.
- **The grader's config holds commands, not Python.** `install`, `lint`, `test`, `hidden_test_cmd` and
  `migrate` are plain commands, so they work for any language; `hidden_dir` and `test_dirs` must point
  at that codebase's test layout.
- **The guard reads command text.** Paths under `~/.cargo`, `~/.rustup`, `~/.cache` and any
  `run_allow_write` folder are allowed in commands; other home folders such as `~/go` and `~/.npm` are
  refused unless listed in `run_allow_write`.

## Known limits

- The sandbox is checked on macOS (trials 3–5 in `TRIALS.md`). A repo that downloads from somewhere
  other than PyPI (a Python build from GitHub, model weights, npm) needs `run_allow_domains` or `--allow-domain`; uv's own
  Python downloads come from GitHub and will fail, so the Python a repo needs must already be installed.
- Postgres over TCP is blocked; runs must use the socket URL the harness sets.
- The leak scan also flags GitHub tokens in any tool output and `gh auth` or git credential calls made
  from inside a program.
- Live counts use the usage on each streamed message, which under-counts output until the call ends;
  the final figures come from the result record.
