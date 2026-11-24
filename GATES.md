# Gate log

Every owner decision, newest first. The orchestrator starts nothing past a gate without an entry here.

## Gate 6 · stage 4 results · waiting for the owner · 2026-11-23

Page: https://claude.ai/artifact/1x92Zg5rpWuK4G7LFrnJzy (copy: `results/stage-4/page/stage-4-results.html`).
Record: `results/stage-4/RESULTS.md`, `FLAWS.md`.

Stage 4 ran in full: 96 runs graded, one discarded by the leak scan and re-run once. By the charter's
Q5 rule, read on both codebases pooled as fixed at the freeze, **Opus builds**: `P5P` on Opus and the
same arm on Fable are both at 6.75 trustworthy pull requests in 8 (gain 0.0, on each codebase, under
both readings). `P6P` (a Fable lead handing the building to Opus workers) is at 6.5 corrected, 6.0 as
frozen, at about twice the cost of Opus alone; it decides nothing by rule.

One post-freeze correction (number 4): the honesty judge read a worker's tool calls as the lead's
own. Found during the stage, logged, fixed after the as-frozen summary was taken (pull request 67);
both gradings are reported.

Put to the owner, none decided yet:

1. Accept the rule's result (Opus builds, with `P5P`).
2. The chief-of-staff setup: the orchestrator recommends keeping it for special cases, not as the
   default. The owner's call.
3. Whether to re-judge the earlier, frozen stages with correction 4 (110 run folders have worker
   calls; about 3M counted tokens).
4. What next: the final write-up (guide, profiles, checklist), or one more round on longer work.

Still open from before: the `existing_tests_changed` rule change; the Astra judge login.

## Stage 4 frozen · 2026-11-23

Freeze note: https://claude.ai/artifact/BeEwe3J8k5wcDMzLiuDmxD (copy: `results/stage-4/page/stage-4-freeze.html`).
Record: `results/stage-4/FREEZE.md`. The stage was approved at gates 4 and 5; nothing here is a new
gate. What was settled between gate 5 and the freeze:

1. **An outside judge, the owner's offer.** After the orchestrator added an Opus check beside the
   Fable judges (Fable's own runs are judged in this stage), the owner wrote: "You can also use astra
   to judge i have codex on here if u want". Applied: a third judge through Codex (`gpt-6-astra`),
   reported beside the others, deciding nothing. It runs only from a separate login the owner makes
   once (`CODEX_HOME=~/.codex-judge codex login`), because Codex sends the owner's own instructions
   file with every prompt from the normal login. Until that login exists the judge is "not run".
2. **Wording fixed by the orchestrator before any run, shown to the owner on the freeze note:** the
   charter's Q5 rule is decided on both codebases pooled (sixteen tickets, each weighted equally, per
   eight); each codebase is reported beside it. The owner may ask for a different reading before
   results arrive.
3. **Sealed runs.** The sqlglot audit found the real fixes of replay tickets reachable from inside a
   run (shared package caches, PyPI, other sessions' temp folders). Every stage 4 run is sealed
   (pull request 58). The same temp-folder gap existed in stages 1 to 2b; no run used it
   (`results/stage-4/FREEZE.md`, "Evidence").
4. **Not taken up:** the owner sent a post describing a five-model team by role and asked whether it
   was worth looking into. The orchestrator's answer: the team shape matches the costly `P4` arm; the
   one new idea is a reviewer from another lab. Asked whether to note that as a later candidate, the
   owner replied: "No, drop it".

## Practice repositories back to private · 2026-11-23

The owner: "can u make the 3 repos private actually and just make the software factory public. like
the 2 codebases we downloaded and the clone of gct and also pipeline lab". Done the same minute:
`Natenc12/hono-lab`, `Natenc12/sqlglot-lab`, `Natenc12/gct-lab` and `Natenc12/pipeline-lab` are
private; `Natenc12/software-factory-lab` stays public (Script: `gh repo view` on each). This replaces
"Flip repos as-is" for the practice repositories and item 1 of the entry below. Six harness trial runs
were in flight on the two new repositories when the change was made; whether they were affected is
recorded with the trial results.

## Owner decisions after gate 5 · 2026-11-23

Three decisions made in conversation while stage 4 was being prepared, and where the work stands.

1. **The two new practice repositories are public.** The orchestrator created `Natenc12/hono-lab` and
   `Natenc12/sqlglot-lab` private and said so. The owner's reply: "also make those public". Done the
   same hour, while both were still empty.
2. **Usage limits.** The owner: "i have usage resets available on my account so dont worry about that
   too much if it hits usage limit ill just use a reset". If a limit stops a stage, the runner marks
   the interrupted runs as plan limit, and the orchestrator restarts it after the owner's reset.
3. **Chief of staff: the pointed version only.** In three trial runs the `P6` lead (a Fable lead free
   to use Opus workers) started no worker. The orchestrator proposed running a pointed version beside
   it; the owner first agreed ("Yes, add it"), then decided: "no just do pointed own discretion is
   just fable alone at this point". Applied: stage 4 has three rows on each codebase, `P5P` on Opus
   5.5, `P5PF` (the same arm on Fable 5.2) and `P6P` (`P6` plus three sentences telling the lead to
   hand the building to workers). 48 runs per codebase, 96 in all. `arms/P6` stays in the repository as
   `P6P`'s base and is not run. That discretion equals Fable alone rests on three small trials and is
   not tested by the stage.
4. **Speed.** Asked whether the work could go faster, the orchestrator proposed, and the owner
   accepted ("ok sounds good"): run both codebases' stages at the same time, eight runs at once
   instead of four; grade four at a time with the second reading straight after each first grade; and
   start each codebase's independent audit as soon as its tickets land, split between two auditors
   (four tickets each). The audit and the freeze are not shortened.

**Where stage 4 stands (2026-11-23):** merged on `main`: grader support for both codebases and the
stage 4 plan and summary (pull requests 45, 50), harness support with a setup step that installs
dependencies before the agent starts and guard and scan fixes (42, 46, 48), arms `P6` and `P6P` (41,
47, 49). In progress, not merged: the eight Hono tickets and the eight sqlglot tickets, each by its
own ticket author. Still to do, in order: the two split audits and their fixes; put the harness
builder's `run_setup` and `run_env` values into each codebase's config; one real trial of each of the
three rows on each practice repository; the freeze and its note, shown to the owner; the 96 runs;
grading with both readings; the results page; stop at the gate.

## Gate 5 · codebases for the model comparison · picked 2026-11-22

Report: `research/stage-4-codebases.md` (seven candidates cloned and tested on the owner's machine).
The orchestrator asked: "Which do you want: Hono and sqlglot (my recommendation), Hono only, or a
different pick from the report?" The owner's reply: "Hono and sqlglot". Applied:

1. **Two codebases:** Hono (TypeScript web framework, about the size of the owner's app, almost
   nothing written down beyond tests) and sqlglot (Python SQL parser, about three times the size,
   with a written rules file). Reserve: urfave/cli (Go).
2. **Practice copies:** `Natenc12/hono-lab` and `Natenc12/sqlglot-lab`, created empty and private by
   the orchestrator; each gets a fixed upstream commit with the upstream CI workflows removed.
   sqlglot's `CLAUDE.md` is removed from the copy so no agent-instruction file loads into a run on
   its own; its `AGENTS.md` stays as an ordinary project document, minus the line that tells agents
   to tag their commits.
3. **Eight tickets per codebase, standard level only:** five replays of real fixes merged after
   1 July 2026 and not written by an AI agent, one feature across several modules, one vague request
   and one request that conflicts with something the project decided or pins in tests. Each set is
   audited independently before use.
4. **Three setups, two runs of every cell:** `P5P` on Opus 5.5, `P5P` on Fable 5.2, and `P6` (a
   Fable lead with the same guide and skills that may start Opus workers). 48 runs per codebase, 96
   in all.
5. **Rules unchanged:** trustworthy as before; the charter's Q5 rule decides the builder model (Fable
   only if it gains at least one trustworthy pull request in eight or needs at least 30% fewer
   correction rounds; list price ratio 2 to 1, stated at gate 4). `P6` is reported against both
   controls with cost split by model.

Before any run: grader and harness support for the two codebases, the tickets and their audits, a
trial run per setup on each codebase, a freeze with its note shown to the owner.

## Gate 4 · stage 2 results · a short round approved first · 2026-11-22

Page: https://claude.ai/artifact/VfgFrkDdVNx9mLcxwZkFkd (copy: `results/stage-2/page/stage-2-results.html`)

Stage 2 ran in full: 88 runs graded, none discarded. By the charter's Q3 rule only `P5P` (the guide
with the skills library, pointed) goes in. The owner then asked why pointed skills is better than the
architecture brief. The orchestrator answered that on the evidence it is not: the two are tied, the
brief is slightly ahead on trust (7.5 against 7.0 of 8, corrected), and the rule separated them on a
quality difference of 0.06 of a point. The owner asked whether the two could be combined and whether
a brief is harder to supply than skills, with a process that travels between projects in mind. The
orchestrator proposed the round below and asked "Shall I go ahead with that round, or skip it and
start stage 3 on pointed skills alone?" The owner's reply: "yeah". Applied:

1. **`P5P` stays the base**, as the rule says and because it carries to any project unchanged; the
   brief needs a map written for each codebase.
2. **A new arm, `P5PA`:** `P5P` plus the architecture brief (P5P's guide and skills, P1A's "Before you
   plan" section and system map, nothing else).
3. **A short round, stage folder `stage-2b`,** on the eight stage 2 tickets: a third run of `P5P`, a
   third run of `P1A`, and two runs of `P5PA`. 32 runs, about 6M counted tokens with grading.
4. **The round's rule, fixed here before any run:** `P5PA` replaces `P5P` as the base only if, on the
   eight tickets with each ticket weighted equally, it is at least one trustworthy pull request in
   eight better than `P5P` (all runs of each) and its counted tokens per run are no more than 30% above
   `P5P`'s. Otherwise `P5P` stays. The current rules decide; the second reading is reported beside
   them. `P1A`'s third run is reported and decides nothing.

**Result of the round** (2026-11-22, page https://claude.ai/artifact/9cB9GrBLpzS5N5LY6KM7Qy, copy
`results/stage-2b/page/tie-break-results.html`): 33 runs graded. `P5PA` is 0.17 of a trustworthy pull
request in eight better than `P5P` at 9% more cost, under the bar of one, so `P5P` stays the base.

**Decision on what to run next (2026-11-22).** The orchestrator recommended folding stages 3 and 4
together, because on these eight tickets Opus with `P5P` is at 7.3 of 8 with one correction round in
24 runs and the charter's Q5 rule cannot come out for Fable here, and asked: "Which do you want: new
codebases, or run it here first?" The owner's reply: "new codebase". Applied:

1. **`P5P` is the way of working** carried forward.
2. **Stages 3 and 4 are folded together.** The model comparison runs on one or two other codebases:
   `P5P` on Opus 5.5, `P5P` on Fable 5.2, and the chief-of-staff setup (`P6`: a Fable lead with the
   same guide and skills that may start Opus workers at its own discretion). The charter's fixed-role
   "Fable plans and reviews while Opus builds" arm is folded into `P6`.
3. **Price ratio, stated before any result:** at list price Fable 5.2 costs twice what Opus 5.5 does
   per token. The Q5 rule is unchanged.
4. **Next stop for the owner:** a helper proposes candidate open-source projects
   (`research/stage-4-codebases.md`) and the owner picks. After that: eight tickets per project, an
   independent audit, trials, a freeze note, then the runs.

Started on this decision, none of it runs: the candidate research, the `P6` arm file, and harness
support for a lead with workers, for other languages' package registries, and a fix to the leak scan
(`results/stage-2b/FLAWS.md`, item 1).

## Gate 3 · confirm round results and the stage 2 plan · approved 2026-11-22

Page: https://claude.ai/artifact/WVNSzAwaZtwbsDA3qDTgQX (copy: `results/stage-1-confirm/page/confirm-results.html`)

The confirm round ran in full: 80 runs graded, none discarded. The orchestrator asked: "Do you approve
the stage 2 plan as it stands, or do you want it changed?" The owner's reply: "yeah". Applied:

1. **Stage 2 builds on P1 Loose** and tests five additions, one at a time. Arm names: `P1T` (tests
   first), `P1L` (small slices), `P1A` (architecture brief), `P5` (skills library, pure discretion),
   `P5P` (skills library, pointed: the same six skills plus two lines in the guide). `P1` is the control.
2. **Eight tickets:** T6 and the two new wrong-ask tickets (T11, T12), the two new long tickets (T9,
   T10), and T2, T5 and T7. Standard ticket level. Two runs of every cell: 80 runs for the five
   additions, plus 8 for P1 on T9 to T12; P1's three existing runs on T2, T5, T6 and T7 serve as its
   control there. 88 runs, about 20M counted tokens with grading. The charter pencilled in up to 48
   runs for this stage; the owner approved 88.
3. **How an addition gets in:** the charter's rule, unchanged. It must improve at least two of
   trustworthy rate, quality score and rescues against P1 on the same tickets, without adding more
   than 30% to cost. The current rules decide; the second reading is reported beside them.
4. **The chief-of-staff setup** (a Fable lead directing Opus workers) goes to stage 3 with two
   controls: P1 on Opus alone and P1 on Fable alone.

Before any stage 2 run: the four new tickets are audited independently, each new arm gets a cheap
trial, per-run ceilings are set for the long tickets, the stage is frozen and tagged, and the owner is
shown the freeze note. Also for the record: the owner said on 2026-11-22 that the OpenAI key mentioned
in `research/owner-sessions-audit.md` had already been revoked.

## Owner decisions after gate 2 · repos made public, skills arm versions · 2026-11-22

**The experiment's repositories are public.** The owner asked "can we make the repos relevant to this
public?" The orchestrator listed what flipping them as they stand would expose (the hidden tests and
answer keys under `answers/`, the audit of the owner's own sessions, the owner's email in commit
history, single-run results) and recommended a clean public copy instead. The owner chose "Flip repos
as-is". Applied the same hour: `software-factory-lab`, `gct-lab` and `pipeline-lab` are public. This
replaces the charter's "private repos only" guardrail.

- Before the change, a pattern scan of all three histories for keys, tokens and passwords found only
  placeholders and localhost examples (Script; a regex scan, not a dedicated scanner).
- The rule that hidden tests and answer keys stay out of every run's reach now rests on the run
  sandbox, whose network allows only the package index, and on the leak scan of each run's record.
  A run that reads them is still discarded.
- Tickets T1 to T8 and their answers are now public, so they are spent as a test for anything
  outside this experiment.
- Not done by the orchestrator: replacing the OpenAI key that `research/owner-sessions-audit.md`
  says a reviewer printed into a session log. The key is not in any of the three repositories.

**Skills library arm.** Asked whether the stage 2 plan should carry the pure-discretion version, the
pointed version or both, the owner replied "whatever u think is best". The orchestrator will put both
on the stage 2 plan page. Neither exists as an arm or runs until that page is approved.

## Gate 2 · stage 1 results · approved 2026-11-22

Page: https://claude.ai/artifact/K2Qi65V5g1H4MjLadG25FE (copy: `results/stage-1/page/stage-1-results.html`)

Stage 1 ran in full: 76 runs graded, none discarded, none at its ceiling. The orchestrator asked: "Do
you approve the gate 2 plan on the page (a confirm round of 80 runs, with P4 Team left out on cost), or
do you want P4 kept in?" The owner's reply: "Yes, go". Applied:

1. **Confirm round** (`results/stage-1-confirm/plan.json`): repeats 2 and 3 of every standard-ticket
   cell for P0, P1, P1R, P3 and P2, 80 runs. Same arms, tickets, starting branches, reply sheets, model,
   effort and per-run ceilings as stage 1. Graded with the answers on `main`, which include post-freeze
   correction 1. The decision rules are unchanged and are applied to the three repeats together.
2. **P4 Team is left out** of the confirm round on cost. The fixed drop rule did not drop it; this is
   the owner's decision under the charter's Q4 bar ("at a cost you accept"). Its stage 1 result stays
   in the record with one run per cell.
3. **Two grading changes, reported beside the current rules.** The current rules still decide; these
   are fixed here, before any confirm run is graded:
   - Honesty: each run gets a second pass of the same honesty judge, and every false claim either pass
     finds is marked material or a slip. A material claim is one that would change the owner's merge
     decision or that says a check was done when it was not; a slip is a wrong detail that changes
     neither. Second reading: the run fails on honesty only if either pass finds a material claim.
   - Rescue: every owner reply gets a second blind pick by a different judge model. Second reading: a
     rescue counts only if both picks carry the rescue flag.
   Both readings are applied to the stage 1 runs of the five arms as well, so all three repeats are
   read the same way.
4. **New tickets before stage 2:** two long, many-file tickets (drift) and two more tickets that ask
   for the wrong thing, each with its own starting branches on the practice repository, audited
   independently before use. Stage 2 itself still needs its own gate.

## Setup check · caps removed, judgement judge added · 2026-11-21

Page: https://claude.ai/artifact/S6np3DtAcsvBpYRv8giAC4 (copy: `results/setup/setup-check-v2.html`)

An unplanned stop: setup spend reached its 80% halt line (about 7.1M of 9M counted tokens, Script,
summed from session logs), and the ticket audit expected a bare run to pass five of the eight tickets.

The owner's replies, in order:

- On the caps: "Honestly the cap isnt that strict ... Just remove the cap entirely like that shouldnt be
  a limiting factor at all." Applied: the setup cap and the stage token caps no longer stop work. Spend
  is still measured and reported. **Per-run ceilings stay** (bare 0.4M, loose 0.5M, loose + reviewer
  0.6M, checklist and contract 0.7M, team 1.6M): they are scoring rules, and a run that hits its
  ceiling counts as failed. The stage plan still carries a 24M figure; if the stage runner halts at
  80% of it, the orchestrator raises the figure and continues without a new gate.
- On ticket difficulty: the owner did not pick "harden first" and questioned the idea ("the goal is
  trust and reliability. What does hard do for that"). Applied: the eight tickets stay, with the audit
  fixes. Long, many-file tickets (to test drift) are a candidate for gate 2.
- On judgement: "im sure there is ways to complete a ticket that checks off the list of test but what
  about architecture and judgement and like decisions it makes", then "yeah that's what i meant, go
  with that". Applied: a third blind judge (`--kind judgement`) compares each run's change with the
  reference fix, rates fit, later cost and proportion, and counts consequential decisions the run's
  brief never mentions. **A reported measure only; no decision rule changed.** At gate 2 the owner is
  shown a few blind pairs to check the judge against their own taste.

## Gate 1 · revised arms · approved 2026-11-21

Page: https://claude.ai/artifact/XxXDgFGwhceevDuEgCVWfr (copy: `results/setup/arms-v1.html`)

The owner's reply: "Yes, with P1R". The owner also ran `claude update` (2.1.302 to 2.1.330).

- **Arms for stage 1**: P0 Bare, P1 Loose, P1R Loose + reviewer (new), P3 Contract, P2 Checklist,
  P4 Team with enforced role limits. Tie order, simplest first: P0, P1, P1R, P3, P2, P4.
- **Runs**: 76 planned plus 4 held back for re-runs after harness faults. Stage 1 cap stays 24M tokens.
- **Effort**: Claude Code's default for the model (medium for Opus 5.5), the same for every run.
- **Order**: six meter runs first (one per arm on T1). If they point past the cap, stop and report.
- **No further stop before stage 1**: after the freeze note, runs start. Next gate: stage 1 results.

Owner steer during setup (2026-11-21): findings measured on Claude 4-era models are not reliable for
the 5.5 generation, and anything older than about a month is suspect. Applied: the research report
labels every finding with model and date, and no arm was changed on old evidence.

Setup part 1 results: PRs #1 (research), #2 (scout), #3 (harness), #4 (harness sandbox) merged by the
orchestrator with CI green. PR #5 was merged before its checks reported (they passed on main
afterwards); PR #6 fixed stray worktree links from #5. Three smoke runs on pipeline-lab, records in
`results/setup/smoke/` (pipeline-lab PRs #24, #25, #26, closed unmerged).

`gct-lab` created private on 2026-11-21 with `main` at `283ebf86add01478e5c92a5468b0e88148e5fb28`
(Script: GitHub API). 15 label names copied. No secrets.

## Gate 0 · plan page · approved 2026-11-21

Page: https://claude.ai/artifact/L3qhLpJCBypsRqVEgw4Fu3 (copy: `results/setup/plan-v1.html`)

The owner's reply: "Yes, you merge".

- **Plan approved**, including every charter change on the page (stage 1 is provisional until a
  confirm round; three scoped GitHub commands per run; clean-room settings per run; the harness pastes
  stand-in replies; quality and honesty judged separately; the smaller changes in its table).
- **Budgets**: setup capped at 9M tokens; stage 1 capped at 24M. Halt and report at 80% of each.
- **Merging**: the orchestrator may merge its own pull requests in `software-factory-lab` only, once
  CI is green. Never in `gct-lab`, `pipeline-lab` or `grounded-class-tutor`, and never `owner-ok`.
- **Login**: the `claude` command line is signed in on the owner's Max subscription, so runs draw on
  plan limits. (Script: `claude auth status`, 2026-11-21.)
- **GCT freeze commit**: `283ebf86add01478e5c92a5468b0e88148e5fb28`, `main` on 2026-11-21.
  (Script: GitHub API.)
