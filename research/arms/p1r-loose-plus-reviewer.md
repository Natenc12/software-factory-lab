# Arm P1R: Loose plus one fresh reviewer (new process arm)

**Tests:** Q1 and Q2. Also Q4: it is the smallest "team" there is.
**Place in tie order:** between P1 and P3 (P0, P1, P1R, P3, P2, P4).

> **This proposal rests on old-model evidence only.** No study since August 2026 compares a fresh reviewer with self-review on current models. Current evidence shows only that Opus 5.5 is a capable reviewer: it found 74% of real vulnerability-introducing commits in [SecPRBench](https://arxiv.org/abs/2610.33509) (Oct 2026), which gives no false-alarm rate and no self-review comparison. The Mythos 5.2 system card reports the model grades known-Claude work *more harshly* ([Zvi's review of the card](https://thezvi.substack.com/p/fable-and-mythos-52-the-system-card), Nov 2026), which cuts against the old "agents praise their own work" finding. So P1R is a **prediction this experiment tests**: a fresh reviewer adds trustworthy PRs over P1. It is worth running anyway, because the answer decides how short the winning checklist can be.

## Why (old-model evidence, models unnamed or Opus 4.x, 2025 – Apr 2026)

Cognition found that agents work best when only one agent writes code and a reviewer with a clean context loops against it ([source](https://cognition.com/blog/multi-agents-working), read 2026-11-21). Anthropic found a separate sceptical evaluator easier to tune than self-criticism ([source](https://www.anthropic.com/engineering/harness-design-long-running-apps), read 2026-11-21). A model rates its own earlier work as more correct unless it judges in a fresh context ([source](https://arxiv.org/html/2603.04582v1), read 2026-11-21). In race 1, both shapes' reviewers found real bugs: A-T2's reviewer caught a Python 3.10 CSV bug.

P2 and P3 each bundle a reviewer with a lot of other process. P1R tells us whether the reviewer alone gets most of the gain. If it does, the winning checklist can stay short.

## What the run is given

1. P1's one-page guide, word for word.
2. One extra rule at the end of the guide:
   > Before you open the PR, start a fresh reviewer with the file `reviewer-brief.md`. Give it only the ticket text, the diff, and the command to run the tests. Do not give it your plan, notes or reasoning. Fix what it marks as blocking, or say in the PR summary why you did not. Run the reviewer at most twice.
3. `reviewer-brief.md`: P3's reviewer brief from race 1 (`races/race-1/shapes/B/reviewer-brief.md`), with its contract checks replaced by "check the diff against the ticket text". It must run the code and the tests, try at least one input the ticket names, and sort each finding as blocking or note.

The reviewer is a separate subagent, or a separate session if the harness supports it. It has the same model as the builder, read-only file access, and permission to run tests.

## What changes from P0–P4

- Compared with P1: adds only the reviewer step. Same ticket, sandbox and stand-in owner.
- Compared with P3: no contract, no planned owner stop, but the same kind of reviewer.
- Owner stops: same as P1 (when the run chooses), then the merge brief.

## Expected extra cost

About +25–40k tokens per run over P1: one or two reviewer passes on a small diff. That estimate comes from race 1's reviewer runs (73–82k tokens for a full review-only ticket, including setup). Per-run ceiling: 3× the P1 mean, plus 80k.

## How we would know it helped

- It **helps** if P1R beats P1 by more than one trustworthy PR per 8 tickets, or has fewer rescues, without more owner stops.
- It **is enough** if P1R ties with P2 or P3 (within one PR per 8). Then the tie rule picks P1R, and the winning checklist is "loose plus reviewer".
- Also watch: the reviewer's blocking findings that were real bugs, against false alarms (planted-bug key on the review-only ticket; judge on others).
- Behaviour tags to compare with P1: "claimed more than it did", "wrote tests that would pass on broken code".

## Run count

8 tickets × 3 repeats = 24 runs in stage 1, if the budget allows. Otherwise 8 × 1 alongside P1 as a screening run, repeated only if it lands within one PR of the leader.
