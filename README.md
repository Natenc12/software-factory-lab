# software-factory-lab

A private lab for one controlled experiment: which way of working software tickets gives pull
requests the owner can trust, for the least attention and money.

- `CHARTER.md` is the design. It is an export of the live charter doc, which wins if they differ.
- `KICKOFF.md` is the orchestrator's first message.
- `GATES.md` logs every owner decision at a gate.

## Layout

| Folder | What lives there | Can a run see it? |
|---|---|---|
| `arms/` | P0 to P4 and the add-ons, one folder each | only its own arm, copied into its sandbox |
| `harness/` | run launcher, sandbox scripts, cost log | no |
| `tickets/<codebase>/` | ticket texts and reference fixes | only its own ticket text |
| `answers/` | hidden tests and the planted-bug key | **never** |
| `grader/` | scoring scripts, judge briefs, behaviour tags | no |
| `research/` | research and scout reports, with sources | no |
| `results/<stage>/` | grades, owner logs, results pages | no |
| `guide/` | Working with Claude Code, model profiles | no |
| `races/race-1/` | race 1 as it finished, with its history | no |
| `checklist/` | the winning checklist (arm P5P) as the Claude Code plugin `work`; install notes inside | no (runs get `arms/P5P`) |

Run sandboxes live outside this repo, in `~/factory-runs/`. Raw transcripts stay on the owner's Mac
and are not committed.

## Rules

- Changes go through pull requests. CI lints and runs the tests in `tests/`.
- Each stage is tagged when it freezes (`stage-1-frozen`, and so on).
- Never merge in `gct-lab`, `pipeline-lab` or `grounded-class-tutor`. Never add or remove `owner-ok`.
- Every claim in a report says who checked it: Script, CI, Judge, Run says, or Not checked.
