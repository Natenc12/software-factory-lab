# Arms

One folder per arm for stage 1, in tie order: `P0` Bare, `P1` Loose, `P1R` Loose + reviewer, `P3`
Contract, `P2` Checklist, `P4` Team. A run gets an arm with `--arm arms/<name>`; a bare run gets no
`--arm`.

Stage 2 arms are P1's guide word for word plus exactly one addition: `P1T` tests first, `P1L` small
slices, `P1A` an architecture brief (a section plus `SYSTEM-MAP.md`, a one-page map of gct-lab, so this
arm fits only that codebase), `P5` a skills library used at the run's discretion (one sentence plus six
skills), and `P5P` the same library with two lines saying when to use two of the skills.

`P5PA` combines two of them and adds nothing new: P5P's guide followed by P1A's "Before you plan"
section, P1A's `SYSTEM-MAP.md` and P5P's skills, all copied unchanged. Like P1A, it fits gct-lab only.

`P6` Chief of staff is P5P with a lead and workers: P5P's guide followed by a short lead brief, P5P's
skills unchanged, and one general `worker` subagent on `claude-opus-5-5`. The lead decides whether
and when to delegate. The lead's own model (Fable 5.2, `claude-fable-5-2`) is set by the run plan's
`--model`, not by the arm; nothing in the folder names it.

What a run receives from a folder: its top-level `.md` files other than `README.md`, appended to the
system prompt; `agents/*.md`, passed as `--agents`; and, only if the folder has one, `skills/<name>/SKILL.md`
(see `harness/README.md`). Skills are opt-in: each is one file with `name` and `description` front
matter. The run sees every description up front and loads a skill's body only when it calls the skill;
it may use them at its own discretion. Only P5, P5P, P5PA and P6 have skills. Nothing else here is loaded into a run:

- `CHANGES.md`: every departure from the arms' sources, with the reason.
- `SIZES.md`: each arm's word count.
- `P4/hooks/`: the team's per-role hooks, run by Claude Code, never read as instructions.
