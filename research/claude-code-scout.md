# Claude Code scout: what the factory isn't using yet

Checked 2026-11-21 against the official docs (<https://code.claude.com/docs>, read as the Markdown
copies listed in <https://code.claude.com/docs/llms.txt>) and by small trials with Claude Code 2.1.302
on the owner's Mac. Trial details are in [harness-facts.md](harness-facts.md). Where a finding is from
the docs only, it says so.

## The answer in brief

The pipeline uses Claude Code mostly as a chat that is told what to do. The biggest unused lever is
**making the checks mechanical instead of trusting the agent to report them**. Four features do that:

1. A **Stop hook** that refuses to let a run finish until the tests and lint pass.
2. **Per-run agent definitions** whose limits are enforced, so the P4 tester really can't see the
   code.
3. The built-in **`/code-review`** as a second reviewer.
4. A **fixed-shape merge brief** (`--json-schema`) the harness can check before the owner sees it.

A fifth, the **advisor** tool, is a cheap way to answer Q5 without running Fable for every step.

One practical warning comes first: the docs describe a newer Claude Code than the Mac has. Update the
CLI once before stage 1 and freeze it (harness facts item 8). On 2.1.302, `--model fable` silently
runs Fable 5.1, not 5.2.

## The charter's table, checked and corrected

"Used so far" is the owner's note. "Checked" is what race 1's files and the owner's config show
(read 2026-11-21: `races/race-1/runs/ROSTER.md`, `races/race-1/shapes/`, `~/.claude/settings.json`).

| Area | Used so far (owner's note) | Checked | What it offers the factory | Source |
| --- | --- | --- | --- | --- |
| Scripted runs (`claude -p`, Agent SDK) | No | **Correct.** Race 1 runs were background helper agents inside one session, steered with SendMessage, because the app couldn't start sessions over Remote Control | Each run starts as its own process, with a set model, folder, settings, budget cap and full JSON log. All seven harness questions are answered and tried | [headless](https://code.claude.com/docs/en/headless.md), harness facts 1–7 |
| Custom agent definitions | No | **Partly wrong.** Race 1 did start a fresh reviewer agent per run (`shapes/*/SKILL.md` step 6), but as a general agent with a brief file, not a defined agent | `--agents file.json` gives each role its own model, tools, prompt, turn limit, effort and **its own hooks**. Trial t8: a tester role was refused when it tried to read `src/` | [sub-agents](https://code.claude.com/docs/en/sub-agents.md), trial t8 |
| Skills and plugins | Skills yes, plugins no | **Mostly right.** Skills: `work-ticket`, `triage`, `file-issue`. Plugins: none of the owner's own, but an `anthropic-skills` plugin synced from claude.ai loads in every session, and the official marketplace is registered | A plugin bundles skill, hooks, agents and scripts into one installable, versioned unit. `claude plugin eval` scores a plugin with and without it loaded (but has no custom-code graders, so it can't run hidden tests) | [plugins](https://code.claude.com/docs/en/plugins/overview.md), [plugin-evals](https://code.claude.com/docs/en/plugin-evals.md) |
| Hooks | One guard hook | **Correct.** One PreToolUse hook (`guard-main-checkout.py`) in user settings | Stop hooks can block the run from ending (`decision: "block"`, capped at 8 continuations in a row); PostToolUse can run tests after edits; SessionStart can load context; `agent`-type hooks can have a subagent verify a condition (experimental). Hooks passed per run with `--settings` work (t2) | [hooks](https://code.claude.com/docs/en/hooks.md) |
| Worktree isolation | Hand-made worktrees | **Correct.** `shapes/lab-up.sh` makes one worktree per run. Race 1 also hit a clash: helpers shared one scratchpad and a reviewer deleted another run's files | `claude -w <name>` starts a session in its own worktree; `isolation: "worktree"` on an agent role gives that role its own copy. `-p` runs don't clean up their worktrees. Separate processes (scripted runs) also get separate scratchpads, which fixes the race 1 clash | [worktrees](https://code.claude.com/docs/en/worktrees.md) |
| Permission modes and rules | Defaults plus auto mode | **Correct** (`defaultMode: auto` in user settings) | `dontAsk` mode plus allow and deny rules plus the OS sandbox fenced a run completely in trial t5: no network, no writes outside its folder, no `gh` or `git push`, one wrapper script allowed out | [permissions](https://code.claude.com/docs/en/permissions.md), [sandboxing](https://code.claude.com/docs/en/sandboxing.md), trial t5 |
| Plan mode | No | Not checkable from files; no sign of it in race 1 | `--permission-mode plan` keeps its read-only block in `-p` runs (docs). But the run then can't build, so it is a two-call arm: plan in plan mode, then resume in normal mode | [permission-modes](https://code.claude.com/docs/en/permission-modes.md) (doc only) |
| Built-in review commands | No | **Correct** | `/code-review [low…max]` runs in the session, on the plan's usage, and works in `-p` (docs). `/security-review` too. **Ultrareview** gives 3 free runs on Max, then bills to usage credits, which are off for this account. The GitHub **Code Review** app is Team and Enterprise only | [code-review-local](https://code.claude.com/docs/en/code-review-local.md), [ultrareview](https://code.claude.com/docs/en/ultrareview.md), [code-review](https://code.claude.com/docs/en/code-review.md) |
| Scheduled and cloud sessions | No | **Correct** | Cloud scheduled tasks and cloud sessions run on Anthropic's machines with the Mac asleep, on GitHub repos only, counting against the plan. Desktop scheduled tasks run only while the Mac is awake and the app open. For this experiment the runs need the Mac's local `gct-lab` databases, so cloud is a poor fit for stage 1 | [routines](https://code.claude.com/docs/en/routines.md), [desktop-scheduled-tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks.md) (doc only) |
| Desktop app: side sessions, PR auto-fix, pages and docs | Pages yes, others partly | **Correct.** This report is written by a side session; race 1 couldn't use them over Remote Control | Auto-fix watches a PR's CI and review comments and fixes them without polling. Useful for the orchestrator's own PRs; for experiment runs it would change what is measured, so keep it off there | [desktop](https://code.claude.com/docs/en/desktop.md) (doc only) |
| Memory file (`CLAUDE.md`) | Removed from GCT (#178) | Not checked: the GCT repo is off limits to this scout | Loaded into every session; the docs advise under 200 lines and say it is guidance, not enforcement. `.claude/rules/` scopes rules to paths. The clean-room flags in the harness keep the owner's user memory out, but a project `CLAUDE.md` in `gct-lab` still loads, so freeze whether one exists | [memory](https://code.claude.com/docs/en/memory.md) |

**Rows the table is missing:**

| Area | What it is | Fit | Source |
| --- | --- | --- | --- |
| Advisor tool | The working model consults a stronger model at key points; `--advisor <model>`, works in `-p` | Ranked #5 below | [advisor](https://code.claude.com/docs/en/advisor.md) |
| Structured output | `--json-schema` makes the run's final answer valid JSON of a given shape | Ranked #4 below | [cli-reference](https://code.claude.com/docs/en/cli-reference.md) (doc only) |
| `/goal` | Keeps the run going until a model judges a stated condition met; works in `-p` | Weaker cousin of the Stop hook: the judge is a model, not the test suite | [goal](https://code.claude.com/docs/en/goal.md) |
| Agent teams | Several full sessions with a lead and direct messages | **Doesn't spawn under `-p`**, and is experimental. P4 has to use subagents | [agent-teams](https://code.claude.com/docs/en/agent-teams.md) |
| Dynamic workflows | Claude writes a script that runs many subagents | For sweeps across many files, not one ticket | [workflows](https://code.claude.com/docs/en/workflows.md) |
| Effort levels | `--effort low…max` per run, and per role in `--agents` | Must be frozen per arm, or it becomes a hidden variable (Opus 5.5 and Fable 5.2 default to `medium`) | [model-config](https://code.claude.com/docs/en/model-config.md) |

## Top five, ranked by how much each moves the goal

The goal is trustworthy PRs for little owner attention. Race 1's trust failures were about claims:
skipped checks reported as done, overstated tickets repeated, wrong formats. So features that turn a
claim into a checked fact rank highest.

### 1. Check gate: a Stop hook that won't let the run finish until the checks pass

**What it is.** A script in the run's settings file that fires when the agent tries to end its turn.
It runs the project's test suite and lint. If they fail, it returns `decision: "block"` with the
failure output, and the agent must keep working. A PostToolUse hook can also run the fast tests after
every edit. Claude Code caps a blocking Stop hook at 8 continuations in a row, so it can't loop
forever.

**Why it ranks first.** It takes "I ran the tests and they pass" out of the agent's hands. The
behaviour tags "skipped a check it claimed to run" and "claimed more than it did" can't happen for
the checks the hook runs. The owner can trust the "CI" line of the merge brief without opening CI.

**How to test it.** Add-on **+Check gate** on the best one or two process arms in stage 2, beside
tests-first and small slices.
- The run is given: the same brief; the harness adds the hook to the run's settings file. The brief
  doesn't mention it, so it measures the mechanism, not the instruction.
- Questions: Q3 (does an engineering habit help when enforced?) and Q1 (does a mechanical check close
  the gap between bare and rigorous runs?). A cheap variant on P0 bare answers whether a gate alone
  replaces the checklist.
- Extra cost: a test run per stop attempt, plus the extra turns when it blocks. On GCT's suite,
  roughly 5–15% more tokens per run (estimate).
- Watch for: tests that are slow or flaky make the gate block for the wrong reason. Use the public
  suite, never the hidden tests.

Source: <https://code.claude.com/docs/en/hooks.md> (Stop decision control). Per-run hooks loading
was confirmed in trials t2 and t6; the Stop event itself was not triggered in a trial.

### 2. Role agents with enforced limits (`--agents`) for P4

**What it is.** One JSON file per run defines planner, architect, builder, tester and reviewer. Each
has its own model, tool list, prompt, turn limit and hooks. The limits are enforced by Claude Code,
not requested in a prompt.

**Why it ranks second.** P4's premise is that "each role sees only what its job needs". Without
enforcement the tester can read the code and write tests that fit it, which is exactly the "tests
that pass on broken code" failure. In trial t8 a role hook refused the tester's read of `src/`. The
same file makes the team reusable as a plugin later.

**How to test it.** This is how P4 should be built, not a separate arm.
- The run is given: the lead's brief plus `--agents p4-roles.json`. Tester: `Read, Glob, Grep, Write`
  with a hook blocking the code folder; reviewer: no Edit or Write; builder: full tools.
  Optionally `isolation: "worktree"` for the tester.
- Question: Q4, and Q5 when roles get different models (Fable planner and reviewer, Opus builder).
- Extra cost: none beyond P4 itself. Per-role token counts come from grouping the log by
  `parent_tool_use_id`.
- One check worth adding: a P4 variant with the limits removed (same roles, prompts only), to see
  whether enforcement itself matters.

Source: <https://code.claude.com/docs/en/sub-agents.md>; trial t8.

### 3. The built-in `/code-review` as a second reviewer

**What it is.** A ready-made reviewer that ships with Claude Code. It reviews the branch for
correctness bugs at a chosen effort level, runs in the session on the plan's usage, and works in `-p`.

**Why it ranks third.** The reviewer is where race 1 found real bugs (the Python 3.10 line-break bug,
all three planted bugs in T6). If the built-in reviewer finds as much for less effort, the factory
can drop its own reviewer brief. If it finds different things, running both is cheap insurance.

**How to test it.** Add-on **+Built-in review** and a straight comparison on the reviewer tickets.
- The run is given: after the PR is opened, the harness resumes the session with
  `claude -p "/code-review high" --resume <id>`, or runs it as a separate fresh session on the PR
  branch so it can't lean on the builder's reasoning.
- Questions: Q2 (does our reviewer brief earn its keep?) and Q4 (does a fixed reviewer beat a role
  agent?). Score on planted bugs found, false alarms, and tokens.
- Extra cost: one review per PR, likely 30–100k tokens at `high` (estimate; not measured).
- Not worth testing: ultrareview (only 3 free runs, then usage credits, which are off) and the GitHub
  Code Review app (Team and Enterprise only).

Source: <https://code.claude.com/docs/en/code-review-local.md> (doc only; not run in a trial).

### 4. A fixed-shape merge brief with `--json-schema`

**What it is.** The run's final answer must be valid JSON matching a schema the harness supplies:
for example `tests_run`, `tests_passed`, `scope_out_touched`, `owner_questions`, and each claim with
`checked_by: CI | reviewer | builder`. Claude Code retries until the output fits, and the harness gets
it in `structured_output`.

**Why it ranks fourth.** Race 1's most common owner complaints were "wrong format", "where's the PR?"
and "not enough to decide". A schema makes every brief the same shape, and the harness can check the
claims against the log before the owner reads anything (did the run really call the test command it
says it ran?). That cuts owner attention per PR and catches dishonest briefs mechanically.

**How to test it.** Add-on **+Structured brief** on the best process arm.
- The run is given: the same brief, plus `--json-schema brief.schema.json`; the harness renders the
  owner page from the JSON and flags any claim the log contradicts.
- Questions: Q2 (lighter checklist plus a strict output shape versus a long checklist), and the
  owner-attention score.
- Extra cost: small, a few thousand tokens for the final answer and any retries.

Source: <https://code.claude.com/docs/en/cli-reference.md> (`--json-schema`),
<https://code.claude.com/docs/en/agent-sdk/structured-outputs.md> (doc only).

### 5. The advisor: Opus builds, Fable advises at decision points

**What it is.** `--advisor <model>` lets the working model consult a stronger model before
committing to an approach, when stuck, and before declaring done. The advisor sees the whole
conversation. It works in `-p` and on subscriptions.

**Why it ranks fifth.** Q5 asks whether Fable is worth its cost. The charter's mixed arm (Fable plans
and reviews, Opus builds) needs hand-off plumbing; the advisor is the same idea with none. If Opus
plus a Fable advisor gets most of Fable's first-time correctness at a fraction of the cost, that is
the cheapest answer to Q5.

**How to test it.** A fourth model arm in stage 3: **Opus + Fable advisor**, beside Opus alone, Fable
alone and the mix.
- The run is given: the winning process, `--model claude-opus-5-5 --advisor <fable id>`.
- Question: Q5. Score first-try correctness, correction rounds and cost.
- Extra cost: the advisor's calls are billed on top of the main model; they show up per model in
  `modelUsage`.
- Check before stage 3: docs say a Fable advisor can need usage credits "on some plans". On this
  account Fable drew on the plan in trial t9, but confirm with one advisor call first. Needs the CLI
  update (Fable 5.2 needs v2.1.321+).

Source: <https://code.claude.com/docs/en/advisor.md> (doc only).

## Smaller points, one line each

- **Plan mode add-on**: cheap to try as "plan in plan mode, then resume to build", but P2 already
  stops at a plan; low expected gain.
- **`/goal`**: a model-judged "keep going until done"; the Stop hook does the same with the real test
  suite, so prefer the hook.
- **Memory file arm**: "short `CLAUDE.md` versus long checklist" is a fair Q2 variant at zero cost;
  keep it under 200 lines as the docs advise.
- **Plugin packaging**: package the winner (skill, hooks, agents, wrapper scripts) as a plugin in this
  repo and use `claude plugin eval` as its regression test after stage 3.
- **Effort level**: freeze `--effort` per arm; it is a hidden variable otherwise.
- **Fallback model**: `--fallback-model` would silently switch models under load; leave it off so a
  run never changes model mid-way.
- **Prompt cache**: every run pays about 30k tokens up front to cache Claude Code's own prompt;
  `--tools` with only the needed tools makes that smaller and equal across arms.
- **Checkpointing and `/rewind`** are interactive conveniences; no use to unattended runs.
- **Cloud and scheduled sessions**: revisit for stage 4's extra codebases if they are GitHub-hosted
  and need no local database.

## How this was checked

- Docs: about 50 pages downloaded on 2026-11-21 from `code.claude.com/docs/en/<page>.md`, read
  locally. Page links are in each row.
- Trials: t1–t10 in `~/factory-runs/scout-scratch/`, logged in [harness-facts.md](harness-facts.md).
- Race 1 evidence: `races/race-1/runs/ROSTER.md` and `races/race-1/shapes/` (the hidden and answer
  folders were not opened).
