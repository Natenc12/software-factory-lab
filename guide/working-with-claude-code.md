# Working with Claude Code

What this experiment found about getting pull requests you can trust, for the least of your
attention and money. Written 2026-11-23, after stage 4 and gate 6 ("Yes, write it up").

**How to read the tags.** Every figure says where it comes from:
**Script** (counted by a script from the run records), **CI** (GitHub's checks), **Judge** (a blind
model judge), **Run says** (the run's own report, not re-checked), **Not checked**. "k of n" counts
runs. A figure marked *as frozen* is the grading with the code fixed before the runs; *corrected* is
the same runs after a logged, post-freeze correction (each one is in that stage's `FLAWS.md`).
Anything marked **Advice** is my recommendation, not a finding. A general claim rests on at least 3
runs; anything from fewer is marked *single example* or *small sample*.

**What "trustworthy" means here.** A pull request counts only if all four hold: the hidden tests pass
(Script), no trap tripped, such as editing an applied migration or touching an out-of-scope file
(Script), the honesty judge found no false claim in the run's report (Judge), and no reply from the
stand-in owner had to rescue it (Judge, counted by Script: a reply judge picks each reply from a fixed
sheet). A review-only ticket passes on three other checks: every planted bug caught, no false blocking
alarm, no false claim. Source: `grader/verdict.py`.

**Two readings.** The *current* reading decides. The *second reading* (gate 2) judges honesty twice
and fails a run only on a material false claim, and counts a rescue only if two judges agree. Where
the two differ enough to matter, both are given.

**Re-judged figures.** After the stages were published, 80 earlier runs were judged again with worker
calls labelled (`results/final/REJUDGE.md`). This guide gives the published figure and notes the
re-judged one where it differs.

Counted model and method profiles (what each model tends to do, counted across runs) are in
[`results/final/profiles.md`](../results/final/profiles.md). The packaged checklist is in
[`checklist/`](../checklist/), built separately. This guide gives no profile numbers of its own.

---

## The short answer

1. **Work every ticket with the one-page guide plus six small skills, two of them pointed to**
   (arm `P5P`: [`arms/P5P/`](../arms/P5P/)). The guide is 168 words. The two pointed skills are
   *check-the-ask* (after reading the ticket and the code: does the ask clash with a decision, a test or
   a doc?) and *prove-each-claim* (before writing the pull request: every "passes" or "tested" line
   needs a command from this session).
   - On the owner's own app: 22 of 24 runs trustworthy, against 15 of 20 for the guide alone
     (Script and Judge, stages 2 and 2b, eight tickets, corrected; as frozen 20 of 24 and 14 of 20).
     The guide's 20 runs are 8 from stage 2 and 12 from stage 1 and the confirm round.
   - On two codebases it had never seen: 27 of 32 (Hono 15 of 16, sqlglot 12 of 16) (Script and Judge,
     stage 4, Opus).
2. **Opus 5.5 builds.** On two new codebases Opus and Fable 5.2 tied exactly, 27 of 32 trustworthy
   each, under every reading, with the same split by codebase (Script and Judge, stage 4). Opus cost
   $0.95 a run against Fable's $1.37 at list price (Script).
3. **Give the agent a standard ticket, never a one-line request.** A bare run on the rough capture was
   trustworthy in 1 of 7 tickets; on the standard ticket, 5 of 7 (corrected); on a full spec, 6 of 7
   (Script and Judge, stage 1, one run per ticket). A ticket is a few hundred words with "Done when"
   and "Out of scope".
4. **Skip the heavy machinery.** The five-role team cost about seven times the guide's tokens for no
   gain. The long checklist was trustworthy in 14 of 24 runs against the guide's 21 of 24 (on the
   second reading 18 of 24 against 20 of 24; re-judged, 16 of 24 on the current reading), at twice
   the cost, with 2,738 words to read a ticket against 1,468. Before the pull request it stopped you
   8 times as often (24 plan stops against 3 questions, in 24 runs each). Rules for tests first and small slices, a separate reviewer agent, and a Fable lead directing Opus
   workers did not earn their cost. Details below.
5. **Expect to read 1,400 to 2,000 words a ticket and answer a stop every 1.5 to 5 tickets.** With
   `P5P` on Opus on the two new codebases: 1,421 words per ticket, ticket included, and 0.19 stops per
   ticket, all 6 stops in 32 runs real questions (Script, stage 4). On the owner's own app, on eight
   tickets of which four were built to make a good run stop: 1,989 words and 0.67 stops per ticket (16
   stops in 24 runs, 14 real questions). The guide alone on the same tickets: 1,647 words and 0.38
   stops (7 stops in 20 runs) (Script, stages 2 and 2b). Pointing the skills costs about a fifth more
   reading and nearly twice the stops, for 22 of 24 trustworthy against 15 of 20.
6. **Where it still fails:** a request that quietly conflicts with a recorded decision, and an open
   question buried inside an otherwise buildable ticket. **Advice** (not tested: no ticket was
   written that way): write the decision into the ticket, or say "stop and ask about X" in it.

---

## What to put in a ticket

**Finding: a rough request sinks even a good agent; a standard ticket gets most of the way; a full spec
adds a little more for more reading.** From stage 1, the bare arm (`P0`, ticket only) on seven build
tickets, one run each, corrected grading (Script and Judge, [`results/stage-1/RESULTS.md`](../results/stage-1/RESULTS.md),
`corrected/runs.json`):

| Ticket level | What the ticket held | Words to read | Trustworthy |
| --- | --- | --- | --- |
| S0 Rough | The capture as first filed, 66–123 words | lowest | **1 of 7** |
| S1 Standard | Problem, why, scope in and out, decisions, "Done when" | about 400–750 | 5 of 7 (as frozen 4) |
| S2 Full spec | S1 plus worked examples, failure cases, a must-not-change list | about 600–1,130 | 6 of 7 (as frozen 5) |
| S3 Executable | S2 plus acceptance tests already in the branch | about 620–1,160 | 6 of 7 |

What went wrong on rough tickets (Script and Judge, the six that failed): hidden tests failed on 6 of
6, because the run built something other than what was meant. The behaviour judge tagged 3 runs
"over-built" and 2 "guessed" instead of asking. One run edited an applied migration (T7), and two
touched out-of-scope files (T4, T6).

What a full spec did not fix: the one miss at S2 and S3 was T6, the wrong request, at every level
(Script; *small sample*: 3 runs on one ticket, `P0` at S2 and S3 and `P1` at S3). Here a fuller ticket
made the asked-for thing clearer but did not make a wrong ask right.

By the charter's rule a full spec does **not** replace the pipeline: the bare S2 run came within one of
the best process arm but the owner's reading was higher (1,763 words against 1,603 per ticket)
(Script, `decision.q6_full_spec_replaces_pipeline`).

- **The S1 to S2 step is a single example per ticket.** 5 of 7 to 6 of 7 is one run each; don't read
  the one-ticket gap as a law.
- **How the owner already works matches this.** On 21 November all 16 tickets that got built were full
  specs of 382 to 1,538 words, drafted by agents and approved by the owner in four batches (Script,
  [`research/owner-sessions-audit.md`](../research/owner-sessions-audit.md)).

**Advice.** Keep letting an agent turn your one-line request into a standard ticket, and approve the
ticket, not a plan. Make sure the ticket says three things the runs missed when left out:
1. Any decision that is still open, as "stop and ask me about X" rather than "not yet decided" (see
   vague tickets below).
2. Any recorded decision the change touches, by name.
3. What must not change.

---

## Which way of working for which kind of ticket

`P5P` is the recommendation for every kind. The table shows what each kind did, with the runs that
back it. Ticket kinds are defined in [`tickets/README.md`](../tickets/README.md).

| Kind | Example from the runs | What happened | Runs |
| --- | --- | --- | --- |
| Ordinary (bug-fix replays, a feature, a data migration) | gct T2: cap a huge upload body without echoing it back; Hono and sqlglot: five real fixes each, replayed from the commit before | Every arm with a guide does well. On the new codebases all 72 replay and feature runs passed the hidden tests | 72 of 72 hidden-test passes (Script, stage 4) |
| Vague (one decision left open) | gct T5: may one owner have two classes with the same name? | On one ticket where the open point blocked the build, runs asked. On one ticket where it was buried in a buildable ticket, runs built through it (*one ticket each*) | Hono T7: 6 of 6 asked and passed. sqlglot T7: 0 of 6 asked about the open point (2 stopped to ask something else), all 6 failed one hidden test (Judge, counted by Script) |
| Wrong request, obvious | gct T11: "retry transient errors in the worker" when the worker already does; T12 | Everyone catches it | T11 and T12, 12 runs each: 24 of 24 raised it before building, every arm (stage 2); with stage 2b, 32 of 32 (Judge, counted by Script) |
| Wrong request, against a recorded decision | gct T6: index the first 250,000 words of a long upload, against decision record 0029 | Mostly missed unless pointed at check-the-ask (*one ticket*) | Standard ticket, stage 1 and confirm: 0 of 15. Stages 2 and 2b: `P5P` 3 of 3 raised it and `P5PA` (the same skills plus a map) 2 of 2 (*small sample*); `P1` 0 of 3; the other add-ons 1 of 9 (Judge, counted by Script) |
| Long, many files | gct T9: let a student replace an uploaded file, keep versions, restore one; T10: rename "class" to "course" across the API without breaking clients | Every arm with a guide built them; the guide alone lost one run on a false claim in its report, not on the code | `P5P` 6 of 6, `P1A` 6 of 6, `P1` 3 of 4 (Script and Judge, stages 2 and 2b; *small sample*) |
| Review only | gct T8: review a branch with three planted bugs, one visible only when run | All 15 runs found all three planted bugs, with no false alarm. The bare run and the long checklist each lost two of three runs on a false claim in the review report, such as saying `git status` was clean without running it | Trustworthy: P1 3 of 3, P1R 3 of 3, P3 3 of 3, P0 1 of 3, P2 1 of 3 (Judge, stage 1 and confirm). On the second reading one of P2's two is a slip |

What each row means for you:

- **Ordinary tickets.** No method question here: a guide and a standard ticket are enough. The losses
  that remain are report errors, not code errors. In stage 4, outside the vague and wrong-request
  tickets, the losses were five false claims (counts of tests or files, the reach of a type check) and
  two trips of the "existing test changed" trap (Judge and Script, `results/stage-4/RESULTS.md`).
  The second reading rates four of the five as slips only; one (`sqlglot/p5p-t6-1`) is material
  (Judge). `results/stage-4/RESULTS.md` says three.
- **Vague tickets.** sqlglot T7 marked one point "Not yet decided" and left the rest buildable; no run
  asked about it (0 of 6, Judge counted by Script; one ticket). **Advice:** never write "not yet decided" in a ticket. Decide it, or
  write "stop and ask about this before building".
- **Wrong requests.** The difference is where the clash lives. When the code or tests contradict the
  ticket in plain sight, every run sees it. When the clash is with a decision record elsewhere, runs
  mostly miss it unless told to look, which is what check-the-ask does. This rests on one ticket (T6):
  `P1A`, not told, raised it in 1 of 3. sqlglot T8 (a request against the project's "no dependency"
  wording) was raised by 4 of 6 runs, all told to look; the two that built it noted the wording in
  their report as something left for later (Judge counted by Script; Run says).
- **Long tickets.** Runs per arm on T9 and T10: 6 for `P5P` and `P1A`, 4 for `P1`, a small sample.
  `P1`'s one loss (`p1-t10-1`) passed 9 of 9 hidden tests and lost on a false claim, so this is not
  evidence of drift.
- **Review.** Every arm found the bugs. What separated them was honest reporting, on 3 runs each: take
  it as a pattern, not a measure.

---

## Which model when

**Finding: Opus 5.5 builds.** By the charter's rule, fixed before stage 4: Fable builds only if it
gains at least one trustworthy pull request in eight, or needs 30% fewer correction rounds. Gain 0.0,
pooled and on each codebase, as frozen and corrected, under both readings; neither model needed a
correction round (Script, [`results/stage-4/RESULTS.md`](../results/stage-4/RESULTS.md)).

| Row (stage 4, `P5P` way of working) | Trustworthy | List price per run | Counted tokens per run | Minutes per run | Words you read per ticket |
| --- | --- | --- | --- | --- | --- |
| Opus 5.5 builds | 27 of 32 | $0.95 | 63,467 | 14.6 | 1,421 |
| Fable 5.2 builds | 27 of 32 | $1.37 | 55,709 | 10.8 | 1,373 |
| Fable lead, Opus workers (`P6P`) | 26 of 32 corrected, 24 of 32 as frozen | $1.94 | 106,210 | 17.7 | 1,383 |

All figures Script, from `results/stage-4/corrected/summary.json`; trustworthy also Judge.

**Prices.** List prices per million tokens, as used by the grader (`grader/common.py`, which took them from
the `claude-api` skill's model table cached 2026-11-03; Not checked against today's price page):

| Model | Input | Output | Cache write (1 hour) | Cache read |
| --- | --- | --- | --- | --- |
| Opus 5.5 | $4 | $20 | $8 | $0.20 |
| Fable 5.2 | $8 | $40 | $16 | $0.20 |
| Sonnet 5.5 | $2 | $10 | $4 | $0.10 |
| Haiku 5.5 | $0.10 | $0.50 | $0.20 | $0.01 |

Fable is twice Opus per token. Per run it came to 1.4 times, because Fable used about 12% fewer
tokens (Script). On the Max subscription these are estimates, not bills; what you actually spend is
plan usage.

**Fable was faster**, 10.8 minutes a run against 14.6 (Script). If wall time matters more than plan
usage on a given day, that is the one reason to pick it.

**Advice, when to use which:**

- **Opus 5.5 builds** every ordinary ticket. That is what was tested and what won.
- **Fable 5.2 for judging.** The deciding judges here ran on Fable, with an Opus check beside them;
  the two honesty judges agreed on 90 of 97 runs in stage 4, corrected (88 of 97 as frozen) (Judge). This is a description of what
  the experiment did, not a test of which judge is better.
- **Haiku 5.5 for cheap mechanical checks,** such as the scout's and the harness builder's trials of
  Claude Code flags (`harness/TRIALS.md`). Never tested as a builder here.
- **Sonnet 5.5** was not tested.

---

## What not to bother with, and why

Each of these was tried as its own arm against the guide, on the same tickets and the same stand-in
owner. "Cost" is counted tokens per run unless it says list price.

| Thing | Result | Runs and source |
| --- | --- | --- |
| **A team of role agents** (planner, architect, builder, tester, reviewer; `P4`) | 6 of 8 trustworthy against the guide's 7 of 8, at 580k tokens a run against 80k (7.3 times; $7.37 against $1.15 list price). The owner read 2,596 words a ticket against 1,493, and answered 13 stops against 1 | 8 runs, one per ticket (Script and Judge, stage 1 corrected). Dropped from the confirm round on cost by the owner (gate 2) |
| **The long checklist** (today's `work-ticket` style; `P2`) | 14 of 24 against the guide's 21 of 24; on the second reading 18 of 24 against 20 of 24 (6.0 against 6.7 of 8). Re-judged: 16 of 24 on the current reading. 49 stops in 24 runs (24 at the plan, 22 at the merge brief) and 4 rescues; the guide had 3 stops, all real questions, and none needed rescuing. Twice the guide's cost | 24 runs each (Script and Judge, stage 1 and confirm) |
| **Contract first** (`P3`) | 20 of 24, at 2.2 times the guide's tokens, with 31 stops (26 routine) | 24 runs (Script and Judge, stage 1 and confirm) |
| **A rule to write tests first** (`P1T`) | 12 of 16, the same rate as the guide alone (6.0 of 8 each, corrected; as frozen 10 of 16) | 16 runs (Script and Judge, stage 2) |
| **A rule to work in small slices** (`P1L`) | 10 of 16, worse than the guide (5.0 against 6.0 of 8, corrected). Lost both its migration runs (*small sample*: 2 runs; one, `p1l-t7-1`, only to the blunt changed-test trap) | 16 runs (Script and Judge, stage 2) |
| **A separate fresh reviewer agent** (`P1R`) | 20 of 24 against the guide's 21 of 24 (re-judged: 19 of 24), at 1.55 times the tokens. On the owner's real day, reviewers caught blocking problems in 5 of 15 much bigger pull requests (audit), so this may not carry to large changes | 24 runs (Script and Judge, stage 1 and confirm) |
| **Skills offered without pointing** (`P5`) | Used a skill in 3 of 16 runs; 13 of 16 trustworthy. Pointing at two skills (`P5P`) got 16 of 16 runs using them | 16 runs each (Script, stage 2) |
| **A Fable lead handing the building to Opus workers** (`P6P`) | 26 of 32 corrected against Opus alone's 27 of 32, at about twice the list price ($1.94 against $0.95). It started 38 workers in 32 runs | 32 runs (Script and Judge, stage 4) |
| **An architecture brief** (`P1A`: a one-page system map) | Worked as well as pointed skills (22 of 24 each), but needs a map written per codebase. The stage 2 rule put `P5P` in and kept `P1A` out on a quality difference of 0.06 of a point. Adding the brief on top of the skills (`P5PA`, 15 of 16) did not clear the bar of one more trustworthy pull request in eight | 24 and 16 runs (Script and Judge, stages 2 and 2b) |

Why heavy process lost, as far as the records show:

- **More stops, most of them at the end.** The checklist stopped 49 times in 24 runs: 24 plan stops
  and 25 later stops, 22 of them at the merge brief. Of the 33 stops the grader counts as routine (the
  reply was not ticket-specific, or was a rescue), 24 came after the plan stop: 16 asked to merge, 6
  were a final hand-over, 2 were plain approvals. At the plan stop itself, 15 of 24 drew a
  ticket-specific answer, 4 were plain approvals, 3 were the T6 rescue and 2 were out-of-scope replies
  (Judge, counted by Script; owner logs). The guide's runs end at an open pull request with no stop,
  so the owner's merge decision is not counted on its side.
- **More reading.** The checklist and contract briefs ran 2,288 to 2,738 words per ticket; the guide's
  1,468 (Script).
- **More places to make a false claim.** The checklist had 6 runs of 24 with a false claim, against 0
  of 24 for the guide (Judge). Re-judged: 4 of 24. On the second reading three of the six carry slips
  only, which is most of why its gap shrinks there.

**About the lead with workers.** In three trial runs a Fable lead that was free to delegate started no
worker at all (Script, `harness/TRIALS.md`, trials 12–18), so stage 4 ran only the version told to
delegate. **Advice (the orchestrator's recommendation at gate 6, not decided by the owner):** keep the
chief-of-staff setup for special cases, such as work that splits into several independent parts. Don't
make it the default for single tickets. Note that 3 of 32 `P5P` runs started a worker on their own,
through Claude Code's built-in agent tool (Script).

---

## Where your attention goes, and how to spend less of it

**What the experiment measured per ticket** (Script): words you would read (the ticket, the pull
request description, the final message and any stop page), and stops (times the run asked you
something).

| Way of working | Words per ticket | Stops per ticket | Stops that were real questions |
| --- | --- | --- | --- |
| Guide alone (`P1`, stage 1 and confirm, 24 runs) | 1,468 | 0.1 | 3 of 3 |
| Long checklist (`P2`, same tickets) | 2,738 | 2.0 (1.0 before the pull request) | 16 of 49 |
| Contract first (`P3`, same tickets) | 2,288 | 1.3 | 5 of 31 |
| Guide alone (`P1`, stage 2 and 2b tickets, 20 runs) | 1,647 | 0.38 | 7 of 7 |
| Guide and pointed skills (`P5P`, same tickets as the row above, 24 runs) | 1,989 | 0.67 | 14 of 16 |
| Guide and pointed skills on Opus (`P5P`, stage 4, new codebases, 32 runs) | 1,421 | 0.19 | 6 of 6 |

"Real questions" are stops the grader scores as warranted (a ticket-specific reply, no rescue). The
stage 2 and 2b tickets include four built to make a good run stop (T5, T6, T11, T12), so their stop
rates are high for ordinary work. Still, 4 of `P5P`'s 16 stops there were on tickets with no planted
problem (T2, T9, T10). Each ticket is weighted equally (Script).

**What a real day looked like** (from the audit of 21 November; its figures are counted by script or
read from the transcripts by the auditor, [`research/owner-sessions-audit.md`](../research/owner-sessions-audit.md)):

- **Merges cost the most attention.** About 27 owner actions (14 merge messages, about 10 label
  visits, 3 chases) to approve 14 pull requests whose CI was already green.
- **Most messages were go-aheads.** 25 of 40 messages to the orchestrator were five words or fewer.
- **The owner caught 5 errors the agents should have caught, 3 of them direction errors.** The three:
  building on an old version of the app, building a ticket whose fixes were mostly in code about to be
  retired, and treating attacks on one's own desktop app as blocking. They are the "wrong request" kind
  that check-the-ask aims at.
- **Pull request descriptions ran long.** 879 to 2,475 words on 7 pull requests, like the heavier arms
  here, with a video on top.
- **The day used about 660k tokens per pull request.** That is nearer the five-role team (580k a run)
  than the guide (80k). Real pull requests were bigger, so this is not like for like.

**Advice, ranked by attention saved:**

1. **Ask about merges in one batch.** One message, one line per pull request with its risk, then
   "merge all, or pick". The morning's "Merge both" cleared two at once; the evening took 14 trips.
2. **Let the run decide when to ask, and keep your word at merge.** Most of the checklist's routine
   stops were its fixed stop at the end (22 merge-brief stops in 24 runs), not its plan stop (4 plain
   approvals in 24). With the guide, runs asked only when they had a question (3 stops in 24 runs, all
   real) and ended at a pull request. Your merge decision stays; put it in the batch of item 1.
3. **Use prove-each-claim.** The skill asks for each claim beside the command that backs it, and
   "not checked" where there is none. Whether pull request descriptions actually held such a list was
   not counted (Not checked), and stage 4 still had six runs with a false claim while the skill was used
   in all but one run.
4. **Point check-the-ask at your decision records.** Pointed at it, runs raised the T6-style wrong
   request in 5 of 5 (`P5P` 3, `P5PA` 2); without it, 1 of 12 (Judge counted by Script; one ticket).
5. **Keep briefs short.** The guide asks for "what was wrong, what you changed, how you tested it, and
   anything you are unsure of". That came to 1,400 to 2,000 words a ticket including the ticket
   itself.

---

## Claude Code features that did real work here

Everything below ran in the experiment's harness on Claude Code 2.1.330, in about 370 graded runs
across five stages. Setup details are in [`harness/README.md`](../harness/README.md) and the trials
that proved each one in [`harness/TRIALS.md`](../harness/TRIALS.md).

| Feature | What it did here | How to set it up |
| --- | --- | --- |
| **Headless runs** (`claude -p` with `--output-format stream-json --verbose`) | Every run was its own session with a set model, folder and full log; the harness read token use live from the stream | `claude -p "<prompt>" --model claude-opus-5-5 --output-format stream-json --verbose < /dev/null`. Read the last `result` line and check `is_error` |
| **Clean-room flags** | Kept the owner's own skills, hooks, memory and connectors out of every run, so arms differed only by their files | `--setting-sources ""`, `--strict-mcp-config`, `--tools <fixed list>`, auto memory off, and, for an arm without skills, `--disable-slash-commands`. Not `--bare`: it drops the subscription login |
| **Skills shipped as a plugin** | Delivered `P5P`'s six skills. check-the-ask was called in 23 of 24 runs and prove-each-claim in 23 of 24 on the owner's app (Script, stages 2 and 2b); check-the-ask in all 72 replay and feature runs of stage 4, prove-each-claim in all but one (Script) | Put each skill in `skills/<name>/SKILL.md` with a `name` and a one-line `description`, load with `--plugin-dir`, and add `Skill` to `--tools`. Don't pass `--disable-slash-commands`: it turns off every skill. Keep Claude Code's own skills out in the run's settings instead (`disableBundledSkills`, `skillOverrides`, and allow rules for `Skill(work:<name>)` only). Point to the two that matter in the guide, one line each. Write the run's folders into skill bodies in words, never as relative paths |
| **Instructions appended to the system prompt** | Delivered each arm's guide | `--append-system-prompt` with the guide's text |
| **Permission mode `dontAsk`, the OS sandbox, deny rules and a PreToolUse hook** | Fenced every run: network only to the package index, writes only in its own folder, no `gh` or git remote commands except through one wrapper. 2 runs of about 370 were discarded by the leak scan, both false alarms (Script) | In the run's settings file: `"defaultMode": "dontAsk"`, `sandbox.enabled`, `allowUnsandboxedCommands: false`, `failIfUnavailable: true`, an empty or short `network.allowedDomains`. Absolute paths in rules start with `//` |
| **Resume with a reply** (`--resume <session id>`) | Delivered every stand-in owner reply as the same session | Same flags again, plus `--resume <id> -p "<reply>"`. Cost totals carry over |
| **Per-run agent definitions with their own hooks** (`--agents`) | Kept `P4`'s tester from seeing the code, for real: the role's hook refused every read of `src/` (harness builder's trial 6 in `harness/TRIALS.md`; Not checked by me) | A JSON file of agents, each with `model`, `tools`, `prompt` and `hooks`; pass it with `--agents <file>` |
| **Subagents as workers** | `P6P`'s lead started 38 workers in 32 runs; workers ran in the same sandbox | One agent file with the worker's model; the lead starts it with the Agent tool |
| **Sealed runs** | Kept the real upstream fixes of replay tickets out of reach on Hono and sqlglot | `"run_sealed": true` in the codebase config (`harness/README.md`, "Sealed runs") |

**Advice, for your own day-to-day work, outside the harness:**

- **Install the winner as a skill.** The checklist in [`checklist/`](../checklist/) packages the guide
  and the skills. A guide and two pointed skills replace a 1,600-word procedure.
- **Use `dontAsk` plus allow rules for unattended work,** not auto mode, when you want a run that
  cannot drift outside its folder. This is the setup measured here; auto mode was not compared.
- **Features from the scout's list that the experiment did not test:** a Stop hook that blocks
  finishing until tests pass, the built-in `/code-review`, a fixed-shape brief with `--json-schema`,
  and the advisor tool ([`research/claude-code-scout.md`](../research/claude-code-scout.md)). They
  are candidates, with no evidence from these runs.

---

## What this experiment cannot tell you

- **Short tickets.** Average run times went from about 6 minutes (stage 1's bare arm) to 32 (stage 1's
  five-role team); the deciding stage 4 rows averaged 11 to 18 (Script). Real pull
  requests on 21 November were up to 3,019 added lines (Script, audit). Whether the light method holds
  on day-long work is not tested.
- **Two runs per cell, three at most.** Stage 1 had one run per cell; the confirm round brought the
  standard tickets to three; stages 2 and 4 had two. Treat any difference under one trustworthy pull
  request in eight as noise. Most rules did; the stage 2 rule did not (it counts any gain, and it
  separated `P5P` from `P1A` on 0.06 of a quality point).
- **Three codebases.** The owner's app (as `gct-lab`), Hono (TypeScript) and sqlglot (Python). One
  practice app (`pipeline-lab`) was used for smoke runs only.
- **Everything was near the top of the scale in stage 4.** All rows were at 24 to 27 of 32, so the
  test could not separate the models further. The quality and judgement judges did not separate the
  rows either (Judge).
- **A model may know a public fix from training.** The 72 of 72 hidden-test passes are replays of
  public fixes. The replays post-date 1 July 2026, and both models did equally well on them.
- **The outside judge was not run.** The owner offered a third judge from another lab (Codex); it
  needs a separate login that was never made, so it is "not run" in every summary.
- **A model judges honesty.** Judging the same run twice is not perfectly repeatable: two honesty
  passes agreed on "any false claim" in 111 of 120 confirm-round runs (Judge).
- **One stand-in owner policy.** A judge picked each reply from a fixed sheet. A real owner may reply
  differently, especially on the vague tickets.
- **The trap for changed tests is blunt.** It fires on any edit to an existing test, including one
  that strengthens it. As frozen it failed all 12 runs of one stage 2 ticket (T11) until a correction;
  after that it still cost 4 runs their verdict with every hidden test passing and nothing else wrong:
  `stage-2/p1l-t7-1` (not in any `FLAWS.md`), one in stage 2b and two in stage 4 (Script). A fix waits
  for the owner's word.
- **Re-judging moved three verdicts and no decision.** On the owner's word ("Yes, re-judge"), the 80
  runs in stages 1 to 2b with worker calls were judged again with those calls labelled. Three verdicts
  changed on the current reading (`p2-t2-1` and `p2-t7-2` to trustworthy, `p1r-t3-3` to not); none
  moved on the second reading, and no rule came out differently on the deciding reading. The changes
  look as much like the judge's known non-repeatability as the correction
  ([`results/final/REJUDGE.md`](../results/final/REJUDGE.md)).
- **Public tickets.** The tickets and answers of all three codebases are in this public repository,
  so they are spent as a test of anything outside this experiment.
- **Claude Code 2.1.330 and the 5.5 generation.** The owner's steer at gate 1 holds: findings this
  old become suspect after about a month or a new model.

## Sources

[`GATES.md`](../GATES.md); [`results/stage-1/`](../results/stage-1/RESULTS.md),
[`stage-1-confirm/`](../results/stage-1-confirm/RESULTS.md), [`stage-2/`](../results/stage-2/RESULTS.md),
[`stage-2b/`](../results/stage-2b/RESULTS.md), [`stage-4/`](../results/stage-4/RESULTS.md), each with its
`FLAWS.md` and `summary.json`; [`research/owner-sessions-audit.md`](../research/owner-sessions-audit.md);
[`research/skill-libraries.md`](../research/skill-libraries.md);
[`research/claude-code-scout.md`](../research/claude-code-scout.md); [`harness/README.md`](../harness/README.md),
[`harness/TRIALS.md`](../harness/TRIALS.md); [`arms/`](../arms/README.md). Counts by ticket kind were made
from the `run_rows` of each stage's corrected `summary.json` on 2026-11-23.
