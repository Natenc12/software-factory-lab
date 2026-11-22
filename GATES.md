# Gate log

Every owner decision, newest first. The orchestrator starts nothing past a gate without an entry here.

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
