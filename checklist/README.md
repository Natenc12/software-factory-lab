# The winning checklist (plugin `work`)

The way of working that won the experiment: Opus 5.5 with arm P5P, which is a one-page guide plus six
skills, two of them pointed to. This folder is a Claude Code plugin, so it can replace the
`work-ticket` skill in `~/.claude/skills` through a normal reviewed change and be versioned here.

| File | What it is |
| --- | --- |
| `skills/work-ticket/SKILL.md` | The guide. Its body is `arms/P5P/GUIDE.md` byte for byte; only the front matter is new |
| `skills/<name>/SKILL.md` × 6 | `check-the-ask`, `prove-each-claim`, `test-that-bites`, `find-the-cause`, `stay-in-scope`, `fresh-eyes-review`: byte for byte `arms/P5P/skills/` |
| `.claude-plugin/plugin.json` | Names the plugin `work`, the name the harness gave it in every run, so skills are called `work:check-the-ask` and so on, as tested |
| `CHANGES-FROM-WORK-TICKET.md` | What the owner's current skill does, what this does instead, and what the experiment tested |
| `UNTESTED-IDEAS.md` | Small additions the results suggest, kept apart from the tested checklist |

`tests/test_checklist.py` pins the working content to `arms/P5P`, so the two cannot drift apart.
`arms/` stays the record of what ran; change the checklist here, and expect that test to fail until
the change is deliberate.

## What was tested, and what was not

Tested (results in `results/stage-2/`, `results/stage-2b/`, `results/stage-4/`): P5P on gct-lab (24
runs across stages 2 and 2b, 7.3 trustworthy pull requests of 8) and on Hono and sqlglot (in
stage 4: 32 runs, 6.75 of 8 (27 of 32 trustworthy), no rescue and no correction round). Each run got this guide and these skills, plus
the harness's run prompt (`harness/prompts/run.md`), which told it where the ticket, its scratch folder
and the `lab` commands were and how to ask the owner (a `STOP:` line).

Not tested: the plugin itself. In the runs the guide sat in the system prompt from the start; here it
loads when the `work-ticket` skill is triggered ("do #N" and similar). The run prompt's lab plumbing is
not part of the plugin, so the owner's sessions supply those things their own way (see
`CHANGES-FROM-WORK-TICKET.md`, "Packaging").

## Install (the owner's sessions)

From a terminal, once:

```bash
claude plugin marketplace add Natenc12/software-factory-lab
```

```bash
claude plugin install work@software-factory-lab
```

Or inside a session: `/plugin install work --marketplace Natenc12/software-factory-lab`. The repo's
`.claude-plugin/marketplace.json` lists this folder as the plugin `work`. To try it for one session
without installing: `claude --plugin-dir <path to this folder>`.

The old skill in `~/.claude/skills/work-ticket/` has the same name and the same trigger phrases, so
both would answer "do #N". Move it aside (for example rename the folder) as part of the change, after
deciding what to keep from `CHANGES-FROM-WORK-TICKET.md`; nothing here touches it.

## Remove

```bash
claude plugin uninstall work@software-factory-lab
```

```bash
claude plugin marketplace remove software-factory-lab
```

Then move the old `work-ticket` folder back if you want it again.

## How the harness loads it

The harness does not read this folder. It builds the same plugin `work` from `arms/P5P` for each run
(`harness/sandbox.py`, `write_skill_plugin`) and appends the guide to the system prompt. The pin test
keeps this folder equal to that.
