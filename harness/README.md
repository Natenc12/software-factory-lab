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
   wall time, turns, stops, session id, branch, PR number and both commits.

## Known limits

- The sandbox is checked on macOS (trials 3–5 in `TRIALS.md`). A repo that downloads from somewhere
  other than PyPI (a Python build from GitHub, model weights, npm) needs `--allow-domain`; uv's own
  Python downloads come from GitHub and will fail, so the Python a repo needs must already be installed.
- Postgres over TCP is blocked; runs must use the socket URL the harness sets.
- The leak scan also flags GitHub tokens in any tool output and `gh auth` or git credential calls made
  from inside a program.
- Live counts use the usage on each streamed message, which under-counts output until the call ends;
  the final figures come from the result record.
