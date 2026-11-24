# Fact check: the guide (pull request 71) and the checklist (pull request 70)

Checked 2026-11-23 by an independent session that wrote neither draft. Checked at `claude/guide`
`9c1d922` and `claude/checklist` `19c5005`, against `main` `b5a5555`. Nothing in either draft was
changed. Tags: **Script** (recomputed here from the summaries or the run records), **CI**, **Read**
(read by the checker), **Not checked**.

Every figure that comes from a stage was recomputed from the `run_rows` of the stage summaries, and where a summary was not
enough, from the run records under `~/factory-runs/` and the corrected copies under
`~/factory-runs-variants/`. The proofs are short commands or scripts, run from the repo root.

## Summary

| File | Claims checked | Match | Mismatch | Cannot check |
| --- | --- | --- | --- | --- |
| `guide/working-with-claude-code.md` | 108 | 92 | 15 | 1 |
| `guide/re-running.md` | 36 | 35 | 1 | 0 |
| `guide/README.md` | 1 | 1 | 0 | 0 |
| `checklist/README.md`, manifests, skills, `tests/test_checklist.py` | 12 | 11 | 0 | 1 |
| `checklist/CHANGES-FROM-WORK-TICKET.md` | 26 | 21 | 5 | 0 |
| `checklist/UNTESTED-IDEAS.md` | 5 | 4 | 1 | 0 |
| **All** | **188** | **164** | **22** | **2** |

The headline numbers hold. Recomputed from the raw run records (Script): `P5P` 22 of 24 and `P1` 15
of 20 on the owner's app; Opus and Fable 27 of 32 each in stage 4 under both readings and with Opus
as judge; $0.95, $1.37 and $1.94 a run; 63,467, 55,709 and 106,210 counted tokens; 14.6, 10.8 and
17.7 minutes; 38 workers in 32 runs; 0 of 15 on T6; 72 of 72 hidden-test passes; 111 of 120 and 90
of 97 judge agreement. The owner's decisions are reported as `GATES.md` records them.

Six things must be fixed before the owner acts on these drafts. None changes the winner (`P5P` on
Opus). Four of them change how strong the case against the owner's current way of working looks,
and what the owner should expect to read and answer.

## Must fix

Ranked by how much each would mislead the choice of method.

### 1. The long checklist's result is given on one reading only

- **Where:** `guide/working-with-claude-code.md` lines 44 and 184; `checklist/CHANGES-FROM-WORK-TICKET.md` lines 8 to 10.
- **Wrong text:** "14 of 24 against the guide's 21 of 24" and "4.7 trustworthy pull requests of 8", with nothing beside it.
- **Right text:** add the second reading, which gate 2 (item 3) says is reported beside the current
  one: "On the second reading, 18 of 24 against 20 of 24 (6.0 against 6.7 of 8)". The gap in trust
  shrinks from seven runs to two. Three of the checklist's six false-claim runs carry slips only,
  and the second judge did not agree with one of its four rescues. The cost and attention gaps do
  not change (twice the tokens, 2,738 words against 1,468).
- **Why it matters:** `P2` is the stand-in for the owner's own skill. The trust gap is the main
  reason given to replace it, and it is much smaller on the reading the owner asked for.
- **Proof (Script):**

```bash
python3 -c "
import json; S=json.load(open('results/stage-1-confirm/summary.json'))
for a in ('P1','P2'):
    rs=[r for r in S['run_rows'] if r['row']==a]
    print(a, sum(r['trustworthy'] for r in rs), sum(r['trustworthy_second_reading'] for r in rs), len(rs))"
```

  Prints `P1 21 20 24` and `P2 14 18 24`. `results/stage-1-confirm/RESULTS.md` has the same figures (4.7 and 6.0).

### 2. The routine stops are blamed on the plan stop, and most were not plan stops

- **Where:** guide lines 184 ("33 of them routine approvals"), 195 to 196, 44 ("stopped you 16 times
  as often") and 242 to 243; `CHANGES-FROM-WORK-TICKET.md` line 22.
- **Wrong text:** "The checklist's fixed plan stop means the owner approves plans that needed no
  approval: 33 of its 49 stops were routine."
- **Right text:** "The checklist stopped 49 times in 24 runs: 24 plan stops and 25 later stops, 22 of
  them at the merge brief. Of the 33 stops the grader counts as routine, 24 came after the plan stop
  (16 asked to merge, 6 were a final hand-over, 2 plain approvals). At the plan stop itself, 15 of
  24 drew a ticket-specific answer, 4 were plain approvals, 3 were the T6 rescue, and 2 were
  out-of-scope replies." The grader calls a stop routine when the reply is not ticket-specific or is
  a rescue (`grader/verdict.py` line 78); "routine" is not "an approval that was not needed".
- **Also:** "16 times as often" (49 against 3) counts the checklist's merge-brief stop. The guide's
  runs end at an open pull request with no stop, and nothing was merged in the lab, so the owner's
  merge decision is counted on one side only. Before the pull request it is 24 plan stops against 3
  questions, 8 times.
- **Why it matters:** the advice "drop the fixed plan stop" and the size of the saving both rest on
  this. The records show the fixed stop at the end produced most of the routine stops, and the
  checklist keeps the owner's word before merge.
- **Proof (Script):**

```bash
python3 -c "
import json,glob,os,collections
by=collections.defaultdict(collections.Counter)
for st in ('stage-1','stage-1-confirm'):
    for f in glob.glob(os.path.expanduser(f'~/factory-runs/{st}/p2-t*-*/harness/owner-log.jsonl')):
        for i,l in enumerate(x for x in open(f) if x.strip()): by[i+1][json.loads(l)['reply_id']]+=1
for k in sorted(by): print(k, sum(by[k].values()), dict(by[k]))"
```

  Prints stop 1: 24 (`default` 4, `T6-built-as-asked` 3, `out-of-scope-plan` 1,
  `out-of-scope-question` 1, ticket-specific 15); stop 2: 22 (`no-merge` 15, `final` 4, `default` 2,
  `T5-open-decision` 1); stop 3: 3 (`final` 2, `no-merge` 1).

### 3. The review row says the bare run and the checklist missed planted bugs. They did not

- **Where:** guide lines 109 and 128.
- **Wrong text:** "The guide's arms found all three; the bare run and the long checklist missed."
- **Right text:** "All 15 review runs found all three planted bugs, and none raised a false alarm. The
  bare run and the long checklist each lost two of three runs on a false claim in the review report
  (for example, saying `git status` was clean without running it). On the second reading one of the
  checklist's two is a slip." The counts in the row (3 of 3, 3 of 3, 3 of 3, 1 of 3, 1 of 3) are
  trustworthy verdicts and are right. Line 128's "the reviewing arms' advantage" is an advantage in
  honest reporting, not in finding bugs.
- **Proof (Script):**

```bash
python3 -c "
import json; S=json.load(open('results/stage-1-confirm/summary.json'))
for a in ('P0','P1','P1R','P3','P2'):
    rs=[r for r in S['run_rows'] if r['row']==a and r['ticket']=='T8']
    print(a, sum(r['all_planted_bugs_caught'] for r in rs), sum(r['no_false_claim'] for r in rs), len(rs))"
```

  Prints caught-all 3 of 3 for every arm; no-false-claim 1, 3, 3, 3, 1. Each failing run's
  `harness/verdict.json` shows `all_planted_bugs_caught` `{"caught": 3, "planted": 3}` (Read:
  `p0-t8-1`, `p0-t8-3`, `p2-t8-2`, `p2-t8-3`).

### 4. "Expect about 1,400 words and one stop in five tickets" is the new codebases only

- **Where:** guide lines 47 to 49, the table at lines 217 to 222, and line 250.
- **Wrong text:** the table sets the guide alone (stage 1 and confirm, 1,467 words, 0.1 stops) beside
  `P5P` (stage 4, 1,421 words, 0.19 stops), as if pointing the skills cost no attention.
- **Right text:** add the like-for-like row. On the owner's app, on the same eight tickets, each
  ticket weighted equally: `P5P` 1,989 words and 0.67 stops per ticket (16 stops in 24 runs, 14 real
  questions); the guide alone 1,647 words and 0.38 stops (7 stops in 20 runs). `P5P` reads about a
  fifth more and stops nearly twice as often as the guide alone. Four of those eight tickets are
  built to make a good run stop, so 0.67 is high for ordinary work; but 4 of `P5P`'s 16 stops were
  on tickets with no planted problem (T2, T9, T10).
- **Proof (Script):**

```bash
python3 -c "
import json; S=json.load(open('results/stage-2b/summary/summary.json'))
T=['T2','T5','T6','T7','T9','T10','T11','T12']
for a in ('P1','P5P'):
    c=[[r for r in S['run_rows'] if r['row']==a and r['ticket']==t and not r['discarded']] for t in T]
    m=lambda k: sum(sum(r[k] for r in x)/len(x) for x in c)/len(c)
    print(a, sum(map(len,c)), round(m('attention_words')), round(m('stops_total'),2))"
```

  Prints `P1 20 1647 0.38` and `P5P 24 1989 0.67`.

### 5. The checklist says three skill counts are "not in the results files". They are, and two are zero

- **Where:** `CHANGES-FROM-WORK-TICKET.md` lines 23, 26 and 30.
- **Wrong text:** "How often P5P called `stay-in-scope` is not in the results files"; "P5P's count is
  not in the results files"; "use not counted in the results files".
- **Right text:** `P5P` runs that called each skill, stages 2 and 2b (24 runs) and stage 4 (32 runs):
  `check-the-ask` 23 and 32; `prove-each-claim` 23 and 31; `test-that-bites` 5 and 9;
  `fresh-eyes-review` 2 and 3; `stay-in-scope` 0 and 0; `find-the-cause` 0 and 0. No run of any arm
  in any stage called `find-the-cause`.
- **Why it matters:** "Keep, as tested" for `find-the-cause` and "Use the checklist" for
  `stay-in-scope` rest on a skill whose description was in every run and whose body was never
  loaded. The tested thing is the guide plus two skills that did the work and two used now and then.
- **Proof (Script):** `skills_used` in `results/stage-2b/summary/summary.json` and
  `results/stage-4/corrected/summary.json`, key `P5P`; the same tally from `skills_used` in each
  run's `harness/run.json` agrees.

### 6. "Nothing is dropped or kept without a line in this table" is not true

- **Where:** `CHANGES-FROM-WORK-TICKET.md` lines 5 to 6.
- **Right text:** either add the rows below or change the sentence to say the table covers the main
  steps only. Practices in the owner's `SKILL.md` and `NOTES.md` (Read, both in full) with no line:
  1. The `risk-gate` check and the risk labels on every pull request, and naming the risk at intake.
  2. Saying at intake whether the ticket ends in a pull request or a report.
  3. Listing what the "Done when" list depends on that does not exist yet, and running each "Done
     when" check with its result labelled. Both were in `P2`.
  4. Asking at intake what the work is worth and what it costs, and how any reference code was
     made. The audit ranks this first of its suggestions.
  5. "Helper reports are claims; re-run what they claim." In `P2`; stage 4's flaw 2 is this failure.
  6. Commit by path, never everything at once; check the status first.
  7. For a schema change, open data made by the old code with the new code.
  8. The reviewer's rules: findings proven by running, the threat model (realistic failures, not
     crafted attacks), its safety lines (no printing of secrets, generated files only, a scratch
     library), and the reviewer started by someone other than the builder.
  9. How to put a question to the owner: one question, two or three options with a before and after
     from this codebase, a recommendation, plain English, nothing technical on the first screen.
  10. For a ticket that names a GitHub or CI mechanism, check the platform's current rules.
  11. Mark the pull request ready, wait for a clean state before merging, and the required-check
      conventions.
- **Also in this file:** line 26 recommends dropping the mandatory review on `P1R`'s result (6.7
  against 7.0 of 8; on the second reading 6.7 each). The audit of the owner's real day found
  reviewers caught blocking problems in 5 of 15 real pull requests, and says the lab's tickets were
  much smaller (`research/owner-sessions-audit.md` lines 78 to 80). The recommendation should carry
  that line. Line 22 says fixed stops "came with the lowest score": true for `P2` on the current
  reading only (on the second reading `P0` is lowest), and `P3`, which also has a fixed stop, scored
  20 of 24 against the guide's 21.

## Should fix

Guide, `working-with-claude-code.md`:

| Line | Text | Right figure or wording | Proof |
| --- | --- | --- | --- |
| 304 | the trap "cost 3 runs their verdict ... in stages 2b and 4" | 4 runs, in stages 2, 2b and 4: `stage-2/p1l-t7-1` also has every hidden test passing, no false claim, no rescue, and trips only `existing_tests_changed`. It is one of the "both migration runs" `P1L` lost (line 187), and it is not in any `FLAWS.md` | Script: rows with `trustworthy` false, `hidden_tests_pass` and `no_false_claim` true, no rescue, in the stage 2b and stage 4 corrected summaries |
| 292 to 293 | "Any difference under one ... in eight is inside the noise, and the rules treated it so" | The stage 2 rule did not. It counts any difference above zero, and it put `P5P` in and kept `P1A` out on a quality difference of 0.06 of a point (`GATES.md`, gate 4; `grader/summarize.py` lines 357 to 359) | Read; Script: `decision.addons` in `results/stage-2/corrected/summary.json` |
| 117 | "rates three of the five claims as slips" | Four of the five runs carry slips only; one (`sqlglot/p5p-t6-1`) is material. `results/stage-4/RESULTS.md` line 56 has the same "three" | Script: `no_material_false_claim` on the five runs; each `verdict.json` `second_reading` |
| 121 to 123 | "only runs told to look find it" | `P1A`, not told, raised T6 in 1 of 3; on sqlglot T8, 2 of 6 runs told to look built it as asked. "Mostly" would be right. The whole claim rests on one ticket (T6) | Script: reply ids in each `owner-log.jsonl` |
| 105 | "sqlglot T7: 0 of 6 asked" | 0 of 6 asked about the open point; 2 of 6 stopped to ask something else (`p5pf-t7-2`, `p6p-t7-1`, reply `T7-transpile`). Line 118 has it right | Script: owner logs |
| 108, 126 | "The guide alone drifts a little"; "Four runs per arm per ticket pair" | `P1`'s one loss (`p1-t10-1`) passed 9 of 9 hidden tests with no trap and lost on a false claim in its report: not drift. Runs per arm on T9 and T10: 6 for `P5P` and `P1A`, 4 for `P1` | Read: `verdict.json`; Script |
| 106 | "gct T11 ... 24 of 24" | 24 is T11 and T12 together, 12 each (stage 2); with stage 2b, 32 of 32 | Script: owner logs |
| 230 | "The owner caught 5 direction errors" | 5 errors, 3 of them direction errors (the audit, lines 32 to 40 and 86 to 87) | Read |
| 287 | "from about 6 minutes ... to 18" | The five-role team averaged 31.9 minutes a run in stage 1 | Script: `wall_seconds`, row `P4`, stage 1 |
| 263 to 264 | `--disable-slash-commands` beside `--plugin-dir` | An arm with skills runs without `--disable-slash-commands` (it turns off every skill); its settings keep Claude Code's own skills out (`harness/run.py` lines 69 to 75) | Read |
| 264 | "23 of 24 ... (Script, stage 2b)" | Stages 2 and 2b together | Script |
| 168 | "agreed on 90 of 97 runs" | Say "corrected"; as frozen it is 88 of 97 | Script: `check_reading.pooled` in both summaries |
| 33 to 34 | "22 of 24 ... 15 of 20 ... stage 2 and 2b" | Say "corrected" (as frozen 20 of 24 and 14 of 20). `P1`'s 20 runs are 8 from stage 2 and 12 from stage 1 and the confirm round | Script |
| 183, 219, 221 | 2,595; 1,467; 2,287 words | 2,596; 1,468; 2,288 (cut off, not rounded; the `RESULTS.md` files round) | Script |
| 14 to 17, 107 | rescue and "raised it" tagged Script | Both rest on the reply judge's pick, counted by script: "Judge, counted by Script". The four checks are for build tickets; a review ticket has three others | Read: `grader/verdict.py` |
| 224 | "Script and Read" | "Read" is not in the guide's list of tags | Read |
| 50 to 52 | "Write the decision into the ticket, or say 'stop and ask about X' in it" | This is advice, and no run tested a ticket written that way. Mark it Advice | Read |
| 244 to 246 | "Its output is a list of claims, each with the command that backs it" | Not checked by anyone: no figure counts how many pull request descriptions held such a list. Stage 4 still had six runs with a false claim while `prove-each-claim` was used in all but one run | Script |
| 35, 141 | "27 of 32" | Worth adding the split: Hono 15 of 16, sqlglot 12 of 16, the same for Opus and Fable | Script |
| 285 to 312 | limits list | Missing from `results/stage-4/RESULTS.md`: a model may know a public fix from training (the 72 of 72 are replays of public fixes); the outside (Astra) judge the owner offered was not run; the quality and judgement judges did not separate the rows. The Hono and sqlglot tickets and answers are public too, not only gct's | Read |

The guide's own rule (a general claim rests on at least 3 runs, fewer is marked). Claims that break
it or stretch it:

- Line 187, "Lost both migration runs": 2 runs, not marked, and one of the two lost only to the blunt trap.
- Line 107, "`P5PA` ... 2 of 2": 2 runs, not marked.
- Line 105 and line 119: "runs ask when the open point blocks the build; they build through a buried
  one" rests on one ticket for each half (6 runs each, 2 per row). Not marked as one ticket each.
- Lines 107 and 247 to 248: the case for `check-the-ask` on recorded decisions rests on one ticket (T6). Not marked.
- Line 75 to 76, "A fuller ticket ... does not make a wrong ask right": 3 runs on one ticket (`P0` at S2 and S3, `P1` at S3). Not marked.
- Line 108, "The guide alone drifts a little": 1 failing run, and not a drift (above).

`re-running.md`:

- Line 165 to 167, item 8, "The guard misreads heredocs ... Runs work around it": fixed before stage
  4 in pull request 48 ("heredoc bodies and interpreter code are data unless a shell runs them"),
  which is in tag `stage-4-frozen`; `harness/README.md` "Known limits" describes the fixed behaviour.
  Say it was fixed. Proof: `git merge-base --is-ancestor 8e69697 stage-4-frozen`.

Checklist:

- `CHANGES-FROM-WORK-TICKET.md` line 24 and `UNTESTED-IDEAS.md` line 10, "five false claims, all
  three rows together": five is outside T7 and T8. In all, six runs have a false claim in the
  corrected grading (`hono/p6p-t7-3` is the sixth); nine as frozen. "Mostly counts" is right: four
  of the five are counts of tests or files.
- `CHANGES-FROM-WORK-TICKET.md` line 25: "6.5 of 8" for `P6P` is the corrected figure; as frozen 6.0.
- `checklist/README.md` line 44, `/plugin install work --marketplace Natenc12/software-factory-lab`:
  the `--marketplace <source>` option exists on the command line (`claude plugin install --help`,
  2.1.330). The in-session slash form was not tried, so it is counted as "cannot check".
- `claude plugin validate` passes on both manifests with warnings: no icon, no licence file, no
  marketplace description, no plugin author. None blocks an install.

## Checked and fine

- **Stage 4 table and the model rule** (guide lines 134 to 162): every cell recomputed from each
  run's `harness/run.json` and `verdict.json`, as frozen and corrected. `python3 -m grader.summarize
  stage-4-hono stage-4-sqlglot --out-dir <scratch>` reproduces `results/stage-4/as-frozen/summary.json`
  exactly, and with `--runs-root ~/factory-runs-variants/corrected4` the corrected one.
- **Prices:** the table equals `PRICES` in `grader/common.py`; applied to each run's tokens it gives
  the list prices reported, and for Fable runs it equals the command line's own cost figure.
- **Ticket levels** (lines 39 to 86): 1, 5 (4), 6 (5) and 6 of 7; word ranges; the six rough-ticket
  failures and their traps and tags; 1,763 against 1,603 words.
- **Ticket kinds** (lines 102 to 109), apart from the items above: 72 of 72; Hono T7 6 of 6; T6 0 of
  15, 3 of 3, 2 of 2, 0 of 3, 1 of 9; long tickets 6, 6 and 3 of 4; sqlglot T8 4 of 6.
- **What not to bother with** (lines 181 to 207), apart from the items above: every count, ratio and
  price in the nine rows; 6 of 24 against 0 of 24 false-claim runs; three trial runs with no worker.
- **The real day** (lines 224 to 236): every figure matches `research/owner-sessions-audit.md`.
- **Claude Code features** (lines 256 to 281): all 374 run folders record version 2.1.330; two leak
  scans not clean, both logged as false alarms; flags match `harness/run.py`, `harness/README.md` and
  `harness/TRIALS.md`; the untested features match the scout's list.
- **Owner decisions:** gate 6 ("Yes, write it up", Opus builds with `P5P`), gate 2 (`P4` left out on
  cost), gate 4 (the bar of one in eight), the chief-of-staff advice marked as the orchestrator's,
  the trap fix and the re-judging both left with the owner, the gate 1 steer. All as `GATES.md` has them.
- **Tags:** right everywhere except the items above.
- **`re-running.md`:** every command's flags match its `--help`. Tried: `grader.make_plan stage-4`
  for both codebases (48 runs, three rows, stage name `stage-4-<codebase>`), the plan-editing script
  (stage renamed, 32 runs left, 16 on the new model), `--row-ceiling`, and `grader.summarize`. The
  test command is the one in `.github/workflows/ci.yml`. Items 1 to 7 and 9 to 17 of "Things that
  bit us" match their sources; 37 of 47 and 2 recomputed from `second-reply-picks.jsonl`.
- **Checklist:** `diff -r arms/P5P/skills checklist/skills` shows only the added `work-ticket`
  folder; the six skill files are identical byte for byte. `checklist/skills/work-ticket/SKILL.md`
  is `arms/P5P/GUIDE.md` byte for byte after four added lines of front matter (`---`, `name:
  work-ticket`, a `description:` with the old skill's six trigger phrases, `---`); same SHA-256.
  `arms/P5P` has not changed since tag `stage-2-frozen`, and a stage 4 run's own copy equals it.
  Tests on the branch as CI runs them: 322 passed, lint and format clean; CI is green on both pull
  requests. The plugin name `work` is the one in each run's control folder. Every other stage and
  count cited in `CHANGES-FROM-WORK-TICKET.md` and `UNTESTED-IDEAS.md` matches; nothing in
  `UNTESTED-IDEAS.md` is presented as tested.

## Not checked

- Today's public price page (the guide says so itself), and the figures in the audit of the owner's
  day against the session transcripts: they were checked against the audit document only.
- Anything that spends model tokens or touches GitHub: `harness.stage`, `harness.run`, any judge,
  `grade_stage4.sh`, `grader.dryrun`, `harness.sandbox down`. Their flags were read from `--help`
  and the scripts were read; none was run.
- Installing the plugin, adding the marketplace, and whether the `work-ticket` skill triggers and
  loads the guide in a real session. The in-session `/plugin install` form.
- The 166 GB disk figure, and the four earlier verdicts a rough search says correction 4 might move.
- Whether the judges' findings are right. Verdicts were taken as recorded; only the counting was redone.
- `results/final/profiles.md`, which both guide files link to. It is not on `main` yet (pull request 72).
