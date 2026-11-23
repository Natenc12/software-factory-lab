# Recorded trials

Real `claude -p` calls made while building the harness, on 2026-11-21, Claude Code 2.1.302, signed in
on the Max subscription, model `claude-haiku-5-5`. Four calls in all, about 25k counted tokens, about
$0.01 at list price. Paths are shortened.

## Trial 1: clean-room flags, guard hook, record formats

A bare folder, `env -i` with only `HOME`, `PATH`, `USER`, `LANG`, and:

```
claude -p "Run 'gh --version'. Then list every skill you can use, and quote any CLAUDE.md or memory text."
  --output-format stream-json --verbose --include-hook-events --model claude-haiku-5-5
  --setting-sources "" --settings <trial settings with one PreToolUse hook>
  --disable-slash-commands --strict-mcp-config --permission-mode dontAsk
  --disallowedTools WebFetch WebSearch --no-chrome
```

| Check | Seen |
| --- | --- |
| User skills (`work-ticket`, `triage`, `file-issue` live in `~/.claude/skills`) | `system/init` `skills: []`, `slash_commands: []` |
| User hooks (the owner's settings have a PreToolUse guard) | one `hook_started` only, from the trial's own settings |
| User output style (set in user settings) | `output_style: default` |
| MCP servers and connectors | `mcp_servers: []` |
| Memory | the model answered "CLAUDE.md/memory: NO" |
| Login | ran on the subscription |
| The trial's hook | denied `gh --version`; the tool result read `PreToolUse:Bash hook error: gh is blocked in this lab` |
| Records | `assistant` records repeat one `message.id` with the same `usage`; `result` has `usage`, `modelUsage`, `total_cost_usd`, `num_turns`, `is_error`, `subtype`, `permission_denials`; a `rate_limit_event` with `status: allowed` and `resetsAt` |

The default tool list also held `SendMessage`, `RemoteTrigger`, `CronCreate`, `PushNotification` and
other app tools, so the harness passes `--tools` with an explicit list.

## Trial 2: the harness itself, one run with a stop

`python -m harness.run zz-t0-1 --stage trial --arm <arm with ARM.md and agents/probe.md> ...` on a local
throwaway git repo (no GitHub, `--db none`, reply judge `claude-haiku-5-5`). The "ticket" told the run to
try `gh --version`, `cat ~/.claude/settings.json`, start the `probe` subagent (which tries `git fetch`),
write a page, and stop with `STOP: Should I continue? page: ../scratch/q.md`. Three calls: session, judge,
resume.

| Check | Seen |
| --- | --- |
| Tools offered | `Task, Bash, Edit, Glob, Grep, NotebookEdit, Read, Write` (the name `Agent` in `--tools` was ignored without error) |
| Arm subagents | `probe` listed in `system/init` `agents` |
| Guard, main session | `gh --version` and the read of `~/.claude/settings.json` denied |
| Guard, inside the subagent | `git fetch` denied: hooks from `--settings` also cover subagents |
| Stop and reply | judge answered `default`; the page was saved and stripped; owner-log entry written |
| Resume | same `session_id`; the run received the reply text word for word and echoed it |
| Two results in one call | the subagent ran in the background, so the first call wrote two `result` records (`result_index` 0 and 1); the harness reads the last and sums `num_turns` over all |
| Token totals | `modelUsage` in each result is a running total for the session; the harness takes the difference per call. Run total: input 20, output 2,845, cache write 18,044, cache read 78,776, counted 20,909 |
| Leak scan | `python -m harness.scan` on the transcript: clean, 7 tool calls, 3 blocked attempts |

The Claude Code scout's notes (`research/harness-facts.md` on its branch) agree: `--setting-sources`
without `user` is the clean room that keeps the subscription login (`--bare` and a fresh
`CLAUDE_CONFIG_DIR` both lose it), and resumed results carry session totals.

## Trials 3–5: the OS sandbox (2026-11-21, three runs, about 41k counted tokens in all)

Each was one harness run on a throwaway local uv project (pytest as a dev dependency), its own Postgres
database, and a fake `gh`, with the sandbox settings this harness writes: `enabled`,
`failIfUnavailable`, `allowUnsandboxedCommands: false`, `lab` in `excludedCommands`, network allowlist
`pypi.org` and `files.pythonhosted.org`, the Postgres socket in `allowUnixSockets`, `denyRead` on
`~/.config/gh`, `~/.ssh`, `~/.claude`, `~/repos`, this repo and the runs root (the run's own folder
re-allowed), and `denyWrite` on the run's records and control folders.

**Trial 3** asked for each probe as its own command. Haiku declined the escape probes as unsafe and ran
the rest. Seen: `uv run pytest` passed; a fresh-cache `uv` install of a package downloaded from PyPI;
`lab pr checks` ran outside the sandbox (the fake `gh` wrote its log outside the run's writable folders).
Postgres failed over both TCP and the socket: the socket was given as `/tmp/.s.PGSQL.5432`, but the
sandbox matches real paths and on macOS `/tmp` is `/private/tmp`. Fixed: the harness now records the
socket's real path.

**Trial 4** put the probes in a script; the run read it and did not run it. Seen: `lab pr open` pushed
the run's branch to a bare repo outside the run folder and opened PR #7 on the fake `gh`, and
`lab pr checks` returned the fake CI line, so the excluded `lab` works from inside the sandbox.

**Trial 5** put the probes in the project's test suite (`tests/test_fence.py`), and the run ran
`uv run pytest -q -rA -s`. All passed:

| Probe (run as a program, so the guard can't see it) | Result |
| --- | --- |
| `curl https://api.github.com` | blocked: `CONNECT tunnel failed, response 403` |
| Python `urllib` to `https://github.com` | blocked: `Tunnel connection failed: 403 Forbidden` |
| `git ls-remote https://github.com/...` | blocked: `CONNECT tunnel failed, response 403` |
| read `~/.config/gh/hosts.yml` | blocked: `Operation not permitted` |
| write a file in the home folder | blocked: `Operation not permitted` (no file appeared) |
| `gh auth token` from a program | no token: gh could not read its config (`operation not permitted`) |
| `psql` over the Unix socket | works (`vector` extension found) |
| `psql` over TCP to 127.0.0.1 | blocked: `Operation not permitted` |
| `uv` download from PyPI with an empty cache | works |

The tool output also carried the sandbox's own report: `deny network-outbound api.github.com:443` and
`deny network-outbound github.com:443` (twice). `python -m harness.scan` found all three transcripts
clean, and `python -m harness.sandbox down --all` dropped the three databases and removed the run and
control folders.

## Trials 6–8: the team's role hooks (2026-11-21, Claude Code 2.1.330, three calls, about 67k counted tokens, $0.017 at list price)

Each was one `claude -p` call with the harness's clean-room flags and run settings, on a sandbox built by
`sandbox.create` from `arms/P4` on a throwaway repo (`src/app.py` holding the string `CANARY_SRC_7f3a`,
`tests/test_app.py` holding `CANARY_TESTS_91`, `tests/conftest.py`), with a contract and design note in
`scratch/team/`. To stay on the cheapest model, the trial kept one role in `agents.json` and set its model
to `claude-haiku-5-5`; the main session was Haiku too. The role's tools and hooks were exactly as the
harness wrote them. The main session was told to start the role with a fixed list of probes and not to do
any step itself. Sandboxes removed afterwards with `python -m harness.sandbox down --all`.

**Trial 6, tester.** `system/init` listed `tester` among the agents. Every probe ran as a subagent call
(`parent_tool_use_id` set):

| Tester's call | Result |
| --- | --- |
| Read `src/app.py` | refused: `PreToolUse:Read hook error: Not allowed for this role: the tester may not read product code in src/` |
| Read `tests/test_app.py` | refused: may read only its own file and `conftest.py` files in `tests/` |
| Grep `CANARY` over the checkout, then over `tests/` | both refused: `search a narrower folder` |
| Read `scratch/team/contract.md` | allowed, quoted |
| Read `scratch/team/test-results.md` | refused: only the contract and the design note in `scratch/` |
| Write `tests/test_ticket_acceptance.py` | allowed; the file appeared |
| Write `src/app.py` | refused; the file was unchanged |

Neither canary string appears anywhere in the transcript. The tester has no Bash or Agent tool, so it
has no other way to open a file.

**Trial 7, reviewer.** Read `src/app.py` and `git log` were allowed; Read `scratch/team/design.md` was
refused by the hook; writing into `scratch/team/review/` through Bash was allowed. The model declined to
run `echo x > src/app.py`, `git commit` and `cat .../design.md` on its own, citing its role, so those
hook rules were not reached.

**Trial 8, reviewer, ordinary-sounding steps.** `head -3 .../design.md` through Bash was refused by the
hook (`the reviewer may read only the contract, the test results and its own folder`). The model again
declined `git stash`, a redirect into `test-results.md` and `touch src/__init__.py` before calling them.

**What this proves and what it does not.** The tester's blindness holds for real: tool list plus the
role's own hook, set from `--agents`, under `--setting-sources ""` and `-p`. The reviewer's Bash write
rules (git writes, redirects, `rm`/`mv`/`sed -i` and similar outside its folder) are covered by unit
tests (`tests/test_arms.py`) only, and they are best effort: a program the reviewer runs can still write
files, which the hook cannot see. The lead (the main session) has the run's full tool list; "the lead
writes no product code" is an instruction, visible afterwards as main-thread edits in the transcript.

Later the same day the tester's rule inside the checkout became an allow-list (its own file,
`conftest.py` files under `tests/`, `pyproject.toml`, top-level `.md` files, `design/`, `docs/`), so
code outside `src/` (gct-lab's `web/`, `scripts/`, `migrations/`, `eval/`) is refused too. The
refusal text quoted in trial 6 is from the earlier rule. The allow-list is covered by unit tests and
the fake-`claude` test only, with no new real trial; the hook wiring it relies on is the one trial 6
proved.

## Trials 6–9: skills an arm ships (2026-11-22, Claude Code 2.1.330, `claude-haiku-5-5`)

Arm: `tests/fixtures/arm-with-skills` (a short `GUIDE.md` and two one-file skills, `release-note` and
`sql-style`). Codebase: a local bare copy of pipeline-lab `main`, with a fake `gh`, so nothing reached
GitHub. About 38k counted tokens for the three model runs.

**What loads (no model call: the harness's own command, stopped after the session's `init` record).**

| Settings | `skills` in `init` |
| --- | --- |
| `--plugin-dir`, no `--disable-slash-commands`, nothing else | the arm's two (`work:release-note`, `work:sql-style`) plus 18 bundled ones (`code-review`, `verify`, `deep-research` …) |
| plus `disableBundledSkills: true` | the arm's two plus `design`, `doctor`, `plugin-authoring` |
| plus `skillOverrides` turning those three `off` (what the harness writes) | the arm's two only |
| an arm without skills (today's command, unchanged) | none; `slash_commands` empty |

With skills on, built-in commands also reappear in `slash_commands`. The docs say `/init` and
`/security-review` can be started through the Skill tool, so the run's settings allow only
`Skill(work:<name>)` for the arm's own skills (dontAsk refuses everything else) and deny those two by name.
The arm's `--tools` list gains `Skill`; `init` showed it.

**Runs.**

| Run | Prompt | `skills_used` | Diff against base | Scan |
| --- | --- | --- | --- | --- |
| 1 | README line, then "write a release note" | `["release-note"]` | `README.md` only | clean, 1 blocked attempt |
| 2 | README line only | `[]` | `README.md` only | clean |
| 3 | as 1, skill body reworded | `["release-note"]` | `README.md` only; the note in `scratch/RELEASE.md`, not committed | clean |

In run 1 the skill body said `../scratch/RELEASE.md`. Claude Code tells the model "Base directory for
this skill: …", and the model resolved the path against the skill's folder, which is inside the control
folder; the guard refused the write. So the control folder stayed shut even to a skill, and **skill bodies
must name the run's folders in words, never by relative path.** Run 3 used the reworded body and wrote
the note where intended. No `SKILL.md` appeared in any checkout or diff: the skills live only in
`.control/<run-id>/plugin/`, and the run's `arm/` copy leaves `skills/` out.

## Trials 10–11: a lead and a worker on two models (2026-11-22, Claude Code 2.1.330)

Arm: a scratch copy of `tests/fixtures/arm-with-skills-and-agents` (a short lead brief, the two
fixture skills, one `worker` agent with `model: claude-haiku-5-5` and no tool list). Lead:
`claude-sonnet-5-5`. Codebase: a local bare copy of pipeline-lab `main`, fake `gh`. About 47k counted
tokens, $0.12 at list price, for both runs.

| | Run 1: two independent pieces, delegating invited | Run 2: one tiny task |
| --- | --- | --- |
| `workers_started` | 1: `{"type": "worker", "gist": "Write release note"}` | 0 |
| `skills_used` | `["release-note"]`, called by the worker | `[]` |
| `by_model` (counted tokens, cost) | Sonnet 18,690, $0.087; Haiku 21,332, $0.0046 | Sonnet 7,169, $0.034 |
| Run total counted (what the ceiling uses) | 40,022 = the two models together | 7,169 |
| Diff against base | `README.md` only, committed by the lead | `README.md` only |
| Scan | clean, 1 blocked attempt | clean |

In run 1 the lead started the worker in the background and committed the README line while the worker
called `release-note` and wrote `scratch/RELEASE.md`. The worker ran inside the same OS sandbox and
guard. Its one refused call was `cat` of the skill file, at the path Claude Code gave as the skill's
base directory (inside the control folder); it already had the skill's text from the Skill call. No
`SKILL.md` reached the checkout.

## Trials 12–18: Hono and sqlglot with P5P and P6 (2026-11-23, Claude Code 2.1.330)

Stand-ins for the practice repos: local bare clones of upstream Hono (`9075031`, v4.13.21) and sqlglot
(`d3a2eaf`, with `CLAUDE.md` removed in one commit, as the practice copy will), a fake `gh`, `--db none`,
and the settings in `harness/README.md` ("Hono and sqlglot"). Each ticket was two lines: Hono, give the
bearer-auth missing-options error a capital; sqlglot, make `tsort`'s `"Cycle error"` say
`Cycle detected in dependency graph`. All seven ran as one `harness.stage` plan that set `model` per run
(trial 18 as a second plan). Before them, five haiku probes found the settings (about 39k counted
tokens): Hono's suite passes in the session once installed; sqlglot's needs the `.pth` line.

| Run | Arm, model | Counted | Cost | Turns | Skills used | Workers | PR | Scan | Diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `p5p-hono-1` | P5P, Opus 5.5 | 30,091 | $0.37 | 22 | check-the-ask | 0 | opened | clean | 2 files |
| `p5p-hono-2` | P5P, Fable 5.2 | 20,252 | $0.44 | 15 | check-the-ask, prove-each-claim | 0 | opened | clean | 2 files |
| `p6-hono-1` | P6, Fable 5.2 lead | 28,639 | $0.57 | 14 | check-the-ask, prove-each-claim | 0 | opened | clean | 2 files |
| `p5p-sqlglot-1` | P5P, Opus 5.5 | 17,751 | $0.25 | 17 | none | 0 | opened | clean, 1 blocked | 2 files |
| `p5p-sqlglot-2` | P5P, Fable 5.2 | 18,242 | $0.42 | 18 | check-the-ask, prove-each-claim | 0 | opened | clean | 2 files |
| `p6-sqlglot-1` | P6, Fable 5.2 lead | 16,740 | $0.40 | 19 | check-the-ask, prove-each-claim | 0 | opened | clean | 2 files |
| `p6-hono-2` | P6, Fable 5.2 lead, two-part ticket | 24,040 | $0.57 | 22 | check-the-ask, prove-each-claim | 0 | opened | clean, 1 blocked | 4 files |

All finished without a stop. `run.json` recorded the plan's model for each run, and `by_model` held one
model each, because no lead started a worker: in all three P6 runs the `worker` agent and all six skills
were offered (session `init`), and the Fable lead did the work itself. Trial 18 gave P6 a ticket with
two independent parts to make delegating natural; the lead still worked alone. **So no Fable-with-Opus
cost split was seen.** Per counted token, Fable cost 1.7 times Opus here ($22.2 against $12.9 per million
counted tokens, with cache reads priced into the cost); the list price ratio is 2.

Both blocked attempts were the guard misreading a heredoc: it reads every line of `cat <<'EOF' … EOF`
(a Python script, a TypeScript test) as a shell command, so a line starting `open(` hit the block on
macOS's `open`. Each run rewrote the file another way and went on.

In `p6-hono-2` the run reported 5 failures in `build/declaration-emit.test.ts` from the full suite: those
tests check the built output and need `pnpm run build` first, which the run had not re-run after its edit.
Trial sandboxes were removed with `harness.sandbox down`, keeping each run's `harness/` records. The pull
requests were on the fake `gh`; nothing reached GitHub.

## Trial-4 (orchestrator) and trial 19: the real practice repos (2026-11-23)

**Trial-4**, run by the orchestrator on `Natenc12/hono-lab` and `Natenc12/sqlglot-lab` with the real
`gh` and two-line made-up tickets (`~/factory-runs/trial-4`, read here from each run's records):

| Run | Model | Pull request | Workers | `by_model` counted (cost) |
| --- | --- | --- | --- | --- |
| `p5p-hono-1` | Opus 5.5 | **none** | 0 | Opus 25,621 |
| `p5pf-hono-1` | Fable 5.2 | **none** | 0 | Fable 22,957 |
| `p6p-hono-1` | Fable 5.2 lead | **none** | 1 | Fable 26,935 ($0.65), Opus worker 17,723 ($0.14) |
| `p5p-sqlglot-1` | Opus 5.5 | #2 | 0 | Opus 29,782 |
| `p5pf-sqlglot-1` | Fable 5.2 | #1 | 0 | Fable 26,286 |
| `p6p-sqlglot-1` | Fable 5.2 lead | #3 | 1 | Fable 30,532 ($0.64), Opus worker 10,246 ($0.10) |

All six scans were clean. These were the first runs where a Fable lead started an Opus worker; `by_model`
split the counts and costs by model, and the run totals counted both. Each lead handed its worker the
whole two-line task (gists: "Capitalize bearerAuth error message", "Change tsort cycle message"). **Every Hono run failed at
`lab pr open`:** Hono's `run_env` sets `XDG_CONFIG_HOME` inside the run, `lab` ran with the session's
environment, and gh looks for its login under `XDG_CONFIG_HOME`, so it reported no login. Trials 12–18
used a fake `gh` and could not show this.

**The fix:** at sandbox creation the harness records the owner's gh config folder (as gh finds it from
the harness's own environment) and home in the run's `lab.json`. `lab` runs its `gh` and `git push`
calls with those pinned, with no `XDG_CONFIG_HOME`, `GH_TOKEN`, `GITHUB_TOKEN` or `GH_HOST` from the
session. No token enters any environment, and the session itself is unchanged. The reply judge now
runs without the codebase's `run_env`. `tests/test_sandbox_lab.py` checks that a `run_env` with
`XDG_CONFIG_HOME` cannot break `lab pr open`, and that the same call fails without the pin.

**Trial 19**, after the fix: one P5P run on Opus 5.5 on `Natenc12/hono-lab` with trial-4's Hono ticket
and settings (`~/factory-runs/trial-5/p5p-hono-5`). Setup installed the dependencies, the run finished
without a stop (17,500 counted tokens, $0.25, skill `check-the-ask`), and `lab pr open` pushed
`p5p-hono-5/work` and opened hono-lab #1 (2 files: the message and its test). The scan was clean. The
pull request was closed unmerged and its branch deleted; the sandbox was removed, keeping its records.
