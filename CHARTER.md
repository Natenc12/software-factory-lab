<!-- Exported from the live charter doc https://claude.ai/artifact/Nvmykhm6R3o9Aymk72Log2 at revision 30 on 2026-11-21. The doc is the source of truth; re-export when it changes. The two diagrams are given as text. -->

# Software factory experiment: handoff

2026-11-21 · @Nathan

Hand this doc and its kickoff prompt to a Fable 5.2 session. It runs a staged experiment to find which way of building tickets gives you trustworthy pull requests for the least attention and money: no process, a loose one, a rigorous one, a team of role agents, Opus 5.5 or Fable 5.2.

## Start here

You do five things. After that the orchestrator works alone and only comes back to you at the gates in Stages and gates.

1. **Read this doc and change anything you disagree with.** Comment or edit inline. The questions, arms and decision rules are the parts that matter most.
2. **Check Your decisions at the end. You made them in chat on Nov 21; change any there if you change your mind**.
3. **Start the orchestrator in the desktop app on your Mac, not over Remote Control.** Race 1 could not open new sessions over Remote Control. A local Fable 5.2 session in `~/repos/pipeline-bench` can open sessions, run scripts and watch them.
4. **Paste the kickoff prompt** (Kickoff prompt section below) as the first message of that session, with the model set to Fable 5.2.
5. **Approve its plan page.** The orchestrator's first stop shows you the frozen design and the stage 1 budget. Nothing expensive runs before your yes.

## What race 1 taught us

Race 1 (Nov 20) ran today's checklist (A) against contract-first (B) on 6 practice tickets, 12 Opus runs in all. Both shapes were equally correct. B needed the owner 7 times against A's 10. Full results are on the [benchmark page](https://claude.ai/artifact/Qct9n8wauKwo6GzRx5NnnJ).

The race exposed six weaknesses in how the test itself was set up. Race 2 has to fix each one:

| What happened in race 1 | Why it matters | Fix for race 2 |
| --- | --- | --- |
| Every run passed every hidden test | The tickets were too easy, so correctness could not tell the methods apart | Harder tickets: real history replays, multi-file features, vague specs, long tasks |
| One run per ticket per method | A single lucky or unlucky run can flip a result | 3 repeats per cell in the decisive stage |
| The answer sheet answered A's recommendations and B's differently | B was blocked from fixing a bug it found first | One reply policy for every method: accept the runner's recommendation unless a fixed trigger applies |
| One ticket stated the bug wrongly | Methods that check facts get credit for the test author's mistake | A separate agent audits every ticket and hidden test before the freeze |
| Runs shared a scratch folder, and one deleted another's files | Runs could interfere with each other | Each run gets its own folder, worktree, database and branch prefix |
| Runs were background helpers, not separate sessions | Less like real use, and the model could not be set per run | Each run is its own session with a set model, opened by script with cost logged |

Two facts carry over. An Opus run cost 90k to 115k tokens on small tickets. GitHub needs Pro to lock branches on a private repo, so practice repos run without a lock and no run merges.

## The questions

The experiment answers five questions. Each answer decides something you would otherwise guess at.

| # | Question | What it decides | A result that would change our minds |
| --- | --- | --- | --- |
| Q1 | Does process help at all, or is Opus 5.5 good enough with just the ticket? | Whether to keep building the pipeline | Bare runs match the rigorous ones on correctness, traps and honesty |
| Q2 | Loose or rigorous, and if rigorous, which shape? | How heavy the checklist should be | A short checklist does as well as the long one for fewer tokens |
| Q3 | Do engineering habits matter: tests first, small slices, an architecture brief? | Whether to write them into the checklist | Adding one moves correctness or code quality by a clear margin |
| Q4 | Does a team of role agents (planner, architect, builder, tester, reviewer) beat one agent with a checklist? | Whether to build a factory of roles | The team catches more and needs you less, at a cost you accept |
| Q5 | Is Fable 5.2 worth its extra cost over Opus 5.5? | Which model builds, and which one checks | Fable gets it right first time where Opus needs correcting, saving more of your time than it costs |
| Q6 | Does a fully specified ticket, with clear success and failure criteria, remove the need for a pipeline? | Where to spend effort: on the ticket before the run, or on the process during it | A bare run on a full spec matches the best process on a normal ticket, counting the time the spec took |

One cross-check runs through all five: does the winner still win on a codebase other than GCT?

## What you get at the end

The experiment ends in five things you can use, all kept in the experiment's repo:

| Deliverable | What it is | Example of what it says |
| --- | --- | --- |
| Benchmark reports | A visual results page per stage and one final page, with charts per question, like race 1's | "Contract-first scored 7 of 8 trustworthy PRs, bare scored 4" |
| Model and method profiles | What each model tends to do, counted across runs, not guessed | "On vague tickets Opus guessed in 5 of 6 loose runs, and in 1 of 6 with a contract" |
| Working with Claude Code guide | A practical guide: which method and model to use for which kind of ticket, which Claude Code features help, and what to put in a prompt | "Small bug: loose is enough. Migration: use the contract and a review" |
| The winning checklist | Ready to replace `work-ticket`, through a normal reviewed change | A skill file plus its scripts |
| A kit you can re-run | Harness, tickets, hidden tests and graders, so a new model can be tested the same way | One command per stage |

**How the profiles stay honest.** The blind judge tags every run with behaviours from a fixed list, decided before stage 1. Examples:

- asked before guessing, or guessed on a vague spec
- fixed nearby bugs it was told to leave
- skipped a check it claimed to run
- claimed more than it did
- trusted a wrong fact in the ticket
- wrote tests that would pass on broken code
- over-built beyond the ticket
- stopped when it didn't need to
- **lost proportion:** treated a minor risk as critical and let it steer the work or the owner's attention. Race 1's planning did this: an agent adding `owner-ok` itself became a top fix, when it barely affects the goal

A profile line needs at least 3 observations, and it shows the count. One-off moments go in the run notes, not in the profile.

## How it runs

> **Diagram: who does what.** You (the owner) approve the plan and each gate, and get results pages back.
> The orchestrator (Fable 5.2) plans, freezes, launches, steers and reports. It starts four helpers:
> the research agent (what others do; proposes arms and repos), the ticket makers (an author writes
> tickets, an auditor breaks them), the run harness (one session per run, own sandbox and cap) and the
> grader (scripts first, then a blind judge). The harness starts the runs (Opus 5.5 or Fable 5.2) in
> five arms: P0 Bare, P1 Loose, P2 Checklist, P3 Contract, P4 Team. A stand-in owner answers every
> stop with the same policy for every arm. Runs hand PRs, briefs and logs to the grader.

The orchestrator never builds anything itself. It starts the research agent, the ticket makers and every run as separate sessions. It answers runs only through the fixed stand-in policy, and it reports to you through results pages. Tickets and hidden tests are frozen before any run starts.

## The arms

Each arm is one way of working a ticket. Each run gets the same ticket, the same sandbox setup and the same stand-in owner; only the arm changes.

**Process arms** (stage 1, Opus 5.5 builds):

| Arm | What the run is given | Owner stops | Tests question |
| --- | --- | --- | --- |
| P0 Bare | The ticket and "open a pull request". Nothing else | None required; it may ask | Q1 |
| P1 Loose | A one-page guide: work in a sandbox, add tests, open a PR, write a short summary, ask when unsure | When it chooses | Q1, Q2 |
| P2 Checklist | Today's checklist (A), with fixes 1–3 | Plan, then merge brief | Q2 |
| P3 Contract | Contract-first (B), with the three fixes race 1 found | Only if the contract is wrong, then merge brief | Q2 |
| P4 Team | A lead agent runs five roles. A planner writes the contract, an architect writes a design note, a builder codes, a tester writes tests from the contract without seeing the code, and a reviewer checks. Each role sees only what its job needs | Only if the contract is wrong, then merge brief | Q4 |

**Habit add-ons** (stage 2, added to the best one or two process arms):

| Add-on | What changes | Tests question |
| --- | --- | --- |
| +Tests first | Tests are written and shown failing before any code | Q3 |
| +Small slices | Work lands as a series of small commits, each green, none over about 150 lines | Q3 |
| +Architecture brief | The run reads a one-page system map and the project's decision records before planning | Q3 |

**Spec levels** (Q6). The process arms above all get the same standard ticket. These change only the ticket:

| Level | What the ticket gives the agent | Who writes it | Your cost up front |
| --- | --- | --- | --- |
| S0 Rough | The quick capture as first filed, before triage | An agent, from a conversation | None |
| S1 Standard | Today's ready ticket: problem, scope, decisions, "done when" | The triage agent, with your yes | A few minutes |
| S2 Full spec | S1, plus worked examples (this input gives this result), explicit failure cases and a must-not-change list | The triage agent drafts, you approve | More reading |
| S3 Executable spec | S2, plus acceptance tests already in the branch that must pass. The hidden tests still check beyond them | An agent writes the tests from the examples, you approve the examples | The most up front, the least at merge |

Testing every spec level with every process would take too many runs. Instead, stage 1 runs S0, S2 and S3 with the bare arm (P0), and S1 bare comes from the process arms. That shows how far a better ticket alone gets you. One more set runs S3 with the best process, to see whether process still adds anything on top of a full spec.

Other ways to test how the first prompt is built. The research agent judges which are worth adding:

- **Goal and limits versus step-by-step instructions:** tell it what must be true, or tell it what to do.
- **Interview first:** the agent must ask its questions before starting, and none after.
- **Who writes the spec:** you, or an agent drafting from the rough ticket while you only approve it. This moves your attention to the start rather than removing it.
- **Examples only versus rules only:** show three finished cases, or list the rules.
- **Lean versus rich context:** the ticket alone, or the ticket plus related code, past PRs and decision records.

**Model arms** (stage 3, on the winning process): Opus builds, Fable builds, and a mix where Fable plans and reviews while Opus builds. Q5 is answered by first-try correctness, the number of correction rounds, and cost.

## Stages and gates

> **Diagram: six phases, and you decide at every gate.** Nothing past a gate runs without your yes.
>
> 1. Gate: you approve the plan page.
> 2. **Setup**: repo, research and scout, harness, frozen tickets. 2 smoke runs on pipeline-lab.
> 3. Gate: you approve the revised arms.
> 4. **Stage 1 · Process and spec**: P0 to P4, then spec levels S0 to S3, on 8 GCT tickets. 72 runs, about 14–22M tokens.
> 5. Gate: you see results, approve stage 2.
> 6. **Stage 2 · Habits**: tests first, small slices, architecture brief on the top 1–2 arms. Up to 48 runs.
> 7. Gate: you approve stage 3.
> 8. **Stage 3 · Models**: Opus builds, Fable builds, Fable plans while Opus builds. 24 runs, plus repeats.
> 9. Gate: you approve stage 4.
> 10. **Stage 4 · Other codebases**: the winner and the runner-up on 1–2 other repos. 16–32 runs.
> 11. Gate: you pick the winner.
> 12. **Final**: reports, profiles, Claude Code guide, winning checklist.

Each stage narrows the field, so later stages test fewer arms in more depth. Only stage 1 has a cost estimate yet. The orchestrator gives one for each later stage at its gate, from what the earlier runs actually cost.

## Tickets and codebases

The main codebase is a frozen copy of GCT, so results reflect real code. Copy `grounded-class-tutor` at a fixed commit into a new private repo, `gct-lab`. Runs never touch the real repo.

Each codebase gets 8 tickets, made from this mix:

| Kind | How many | How it's made | What it catches |
| --- | --- | --- | --- |
| History replay | 3 | Take a real bug-fix commit from GCT's history. Reset to the commit before it, write the ticket from the original issue or PR, and use the fix's own tests as the hidden tests | Real difficulty, with a known right answer |
| Multi-file feature | 1 | A feature that crosses at least 3 modules | Whether slicing and planning help on bigger work |
| Vague ticket | 1 | One decision is left genuinely open | Guessing instead of asking |
| Flawed ticket | 1 | The request conflicts with a recorded decision or an existing test | Building the wrong thing as asked |
| Migration on data | 1 | A schema change that must keep existing rows intact | Changes that only fail on real data |
| Review only | 1 | A pull request with 3 planted bugs, one visible only when the code runs | Reviewer catch rate and false alarms |

Before the freeze, a separate auditor agent checks every ticket. Its job is to break them. Each hidden test must fail on the starting code and pass on a reference fix, and every fact in the ticket text must be true.

**Other codebases** (stage 4): one or two open-source projects with strong test suites, in a different language or size from GCT. The research agent proposes candidates and you pick. History replay works on any repo with good commit history, so tickets there come mostly from replays.

`pipeline-lab` (race 1's practice app) stays as a fast smoke test. Any change to the harness runs there first, before it touches real runs.

## Scoring and decision rules

The headline score is the **trustworthy PR rate**: the share of runs whose pull request you could merge without worry. A run counts only if all four hold:

1. The hidden tests pass.
2. No trap was tripped: nothing out of scope changed, no applied migration was edited, and the flawed ticket wasn't built as asked.
3. The merge brief makes no false claim about the work.
4. You didn't have to rescue it.

Every run also records:

| Measure | How it's taken |
| --- | --- |
| Owner stops, split into routine and warranted | Stand-in owner log |
| Correction rounds (times the owner sent it back) | Stand-in owner log |
| Rescues (owner caught a mistake the run should have) | Stand-in owner log, judged by fixed triggers |
| Spec cost: words you must read and approve before the run, plus rounds to agree the spec | Counted from the ticket and its approval log, so a full spec can't win just by moving work onto you |
| Your total attention: spec cost plus stops plus the merge brief, in words read and replies given | Sum of the rows above |
| Code quality, scored 1–5: fits the architecture, readable, tests that mean something | A blind judge agent that sees the diff and brief with the arm's name removed |
| Review catch rate and false alarms | Planted-bug key |
| Tokens and wall time, including tokens spent writing the spec | Session logs |

These rules are fixed before stage 1 and not changed after any result:

- **Ties go to the simpler arm.** An arm within one trustworthy PR of the leader, averaged per 8 tickets, counts as tied. The order from simplest is P0, P1, P3, P2, P4. On a tie, fewer owner stops wins, then lower cost.
- **Process is needed (Q1)** only if the best process arm beats P0 by more than one trustworthy PR per 8 tickets, or P0 needs more rescues.
- **A habit add-on goes in (Q3)** only if it improves at least two of: trustworthy rate, quality score, rescues, without adding more than 30% to cost.
- **Fable builds (Q5)** only if it gains at least one trustworthy PR per 8 tickets, or needs at least 30% fewer correction rounds, at the price ratio the orchestrator states before stage 3. Otherwise Opus builds, and Fable is tested as a planner or reviewer only.
- **A full spec replaces the pipeline (Q6)** only if a bare run on S2 or S3 comes within one trustworthy PR of the best process arm on S1, and your total attention, spec included, is no higher.
- **Generalising (stage 4):** the winner is confirmed if it stays within one trustworthy PR of the best arm on each extra codebase.

## Guardrails

These hold for the orchestrator and every agent it starts. The orchestrator writes them into each run's brief.

- **Never touch the real repos.** Nothing changes in `grounded-class-tutor` or your checkout of it. The existing hook already blocks changes to that checkout, and runs work only in `gct-lab`, `pipeline-lab` and the extra codebase copies.
- **No merges and no** **`owner-ok`****, ever.** Runs end at the merge brief. A hook already asks you before any merge or label change.
- **One sandbox per run:** its own worktree, database, scratch folder and branch prefix (`<arm>-<ticket>-<repeat>/`). No run deletes anything it didn't create.
- **Hidden tests and the answer key stay out of reach.** They live outside every run's folder. The grader checks each transcript for any read of them, and a run that looked is thrown out.
- **Spending caps.** Each run has a token ceiling, about 3× the stage's expected cost per run, and is stopped if it hits it. Each stage has a total budget you approve. The orchestrator halts and reports at 80% of it.
- **One stand-in owner policy for all arms****, applied by a blind judge that sees the run's question without the arm's name****. It accepts** the run's recommended option unless a fixed trigger applies (a raised real problem, an edit to an applied migration, an out-of-scope change). The replies are written before stage 1, and every reply is logged.
- **Private only.** Practice repos are private. No secrets go into tickets, briefs or reports. Your email and personal details stay out of anything published.
- **You stay at the gates.** The orchestrator never starts a new stage, adds an arm or raises a budget without your yes on its plan page.

## One repo on your GitHub

Everything lives in one private repo, `Natenc12/software-factory-lab`, created as the orchestrator's first job once you approve. Race 1's folder, `pipeline-bench`, moves in with its history as `races/race-1/`.

```
software-factory-lab/
  CHARTER.md          this doc, exported
  KICKOFF.md          the orchestrator's first message
  arms/               P0 to P4 and the add-ons, one folder each
  harness/            run launcher, sandbox scripts, cost log
  tickets/<codebase>/ ticket texts and reference fixes
  answers/            hidden tests and the planted-bug key (never given to runs)
  grader/             scoring scripts, judge brief, behaviour tags
  research/           research and scout reports, with sources
  results/<stage>/    grades, owner logs, results pages
  guide/              Working with Claude Code, model profiles
  races/race-1/       what we have so far
```

The repo follows the same rules as GCT:

- **Changes go through pull requests.** CI runs the grader's own tests and a lint pass.
- **Each stage is tagged when it freezes** (`stage-1-frozen`, and so on), so every result points at the exact tickets, arms and scripts that produced it.
- **Results are committed, raw logs are not.** Transcripts stay on your Mac, summaries go in the repo.
- **The winning checklist ships from here.** Once chosen, the skill installs from this repo, so `~/.claude/skills` stops being loose, unversioned files.

The repo stays private. Making any part public is your call, and only after a check that it holds no secrets or personal details.

## Research agent brief

The research agent runs first, before any arm is frozen. Its findings can add, change or drop arms, but only through the orchestrator's plan page and your yes.

**What it looks into:**

1. **Software factories and agent-driven development:** how teams set up agents to take work from ticket to merged code, and what they report actually works.
2. **Role-based agent teams:** setups that mimic a company (planner, architect, builder, tester, reviewer). What each role sees, how work and context pass between them, and where they fail.
3. **The harness itself:** how context, tools and permissions are routed to each agent, and whether that matters more than the prompt.
4. **Engineering habits with agents:** test-first, small slices, architecture docs and decision records, spec-first. What evidence exists, beyond opinion.
5. **How others measure this:** benchmarks built from real commit history, and how they avoid the traps race 1 hit (easy tickets, leaked answers, single runs).
6. **Candidate codebases:** 3 to 5 open-source repos with strong tests and clean history, of different languages and sizes, for stage 4.

**What it hands back:**

- A short report. Every claim links to a page it actually opened, with the date it was read; claims from memory are marked as such.
- For each practice worth testing, a one-page arm or add-on definition the orchestrator can run as written.
- The codebase shortlist, with test-suite size, language and why each fits.
- Known ways these setups fail, so the scoring can watch for them.

It has a token budget and a deadline set on the plan page, and it stops at either.

## Claude Code scout brief

A second researcher runs alongside the research agent. It answers one question: what can Claude Code do that this pipeline isn't using yet? It works from the current official documentation and by trying features, not from memory. Every finding carries the date it was checked.

It starts with the areas below. The first column is what race 1 used, from my notes. The scout confirms or corrects each row:

| Area | Used so far | Worth checking for the factory |
| --- | --- | --- |
| Scripted runs (`claude -p`, the Agent SDK) | No | Starting runs with a set model, folder, permissions and token cap, with cost reported per run |
| Custom agent definitions (an agent's own model, tools and prompt) | No | Making each role in arm P4 a reusable agent |
| Skills and plugins | Skills yes, plugins no | Packaging the winning checklist, its hooks and agents as one installable plugin |
| Hooks | One guard hook | Hooks that run tests after edits, block a stop when checks are unfinished, or load context at start |
| Worktree isolation for sessions and agents | Hand-made worktrees | Built-in isolation instead of scripts |
| Permission modes and rules | Defaults plus auto mode | Tighter per-arm permissions, so a run can't drift |
| Plan mode | No | A cheap "plan first" add-on arm |
| Built-in review commands (`/code-review`, `/security-review`) | No | A ready-made reviewer to compare with ours |
| Scheduled and cloud sessions | No | Long stages that keep running while your Mac sleeps |
| Desktop app: side sessions, PR auto-fix, pages and docs | Pages yes, others partly | Steering many runs and watching CI without polling |
| Memory file (`CLAUDE.md`) | Removed from GCT (#178) | Whether a short project memory beats a long checklist |

It hands back that table completed and corrected, plus a ranked list: the five features most likely to improve the factory, each with how to test it as an arm or add-on. Its findings feed the Working with Claude Code guide.

## Kickoff prompt

Start a new session in the desktop app with the model set to Fable 5.2 and the folder set to `~/repos/pipeline-bench`. Paste this as the first message. A copy is saved at `~/repos/pipeline-bench/KICKOFF.md`. The orchestrator reads this doc live, so whatever you change here before you start is what it follows.

```markdown
You are the orchestrator of a controlled experiment on how AI agents should work software tickets. The owner wants to know which way of working gives pull requests they can trust, for the least of their attention and money. They also want a practical guide to working with Claude Code, and honest profiles of what each model does well and badly. You run it end to end: you plan, build the harness, start and steer every run, play the stand-in owner by a fixed policy, grade, and report. The owner approves at fixed gates and nowhere else.

Read first, in this order:
1. The charter doc, https://claude.ai/artifact/Nvmykhm6R3o9Aymk72Log2: the experiment design (questions, arms, tickets, scoring, guardrails, stages, deliverables, repo layout). It is your spec. Read it with the Claude Docs tools; the owner may have edited it, and the doc beats any older copy. Save an export as CHARTER.md in the new repo, and re-export whenever the owner changes it.
2. ~/repos/pipeline-bench/SPEC.md, runs/ROSTER.md, shapes/, grader/, answers/owner.md: race 1, which you are scaling up. Reuse what works; the charter lists what must change.
3. Race 1's report: https://claude.ai/artifact/Qct9n8wauKwo6GzRx5NnnJ

Models: runners use Opus 5.5 (claude-opus-5-5) unless the arm says Fable 5.2 (claude-fable-5-2). You are Fable 5.2.

The owner's decisions (Nov 21, 2026), already settled: run the full stage 1, all 72 runs (process arms plus spec levels); a separate blind judge agent picks each stand-in reply from the frozen sheet; freeze GCT at today's main; the research agent shortlists 3–5 other repos and the owner picks 1–2; after stage 3 the winner replaces work-ticket through a reviewed pull request.

Your first stop: write a plan page and publish it as an artifact. Make it visual first, in plain English, using the 4-slot strip (Status | From you | Risk | Updated). It shows: the design you will freeze, anything in the charter you would change and why, the exact GitHub actions you will take (starting with creating the private repo Natenc12/software-factory-lab), the token budget for setup and stage 1, and the run schedule. Then stop and wait for the owner's yes. Nothing costly runs before it.

After the yes, in order, stopping at each gate the charter names:
1. Create the private repo with the charter's layout. Move pipeline-bench in with its history as races/race-1/, add CI for the grader, and work through pull requests from then on.
2. Start the research agent and the Claude Code scout as their own sessions, with the charter's briefs. Fold their findings into a revised arms page, then stop for a yes.
3. Build the run harness: a script that starts each run as its own session (Agent SDK or `claude -p`), with a set model, folder, token ceiling and log. Prove it on pipeline-lab with two smoke runs before any real run.
4. Build gct-lab, a private copy of grounded-class-tutor at a fixed commit. Show the exact repo actions first. Have a ticket-author agent make the tickets and hidden tests, and a separate auditor agent try to break them. Freeze everything, tag the repo and record the commit hashes.
5. Run each stage. Reply to runs only from the frozen stand-in owner policy, logging every reply. Grade with scripts first, then a blind judge agent that also tags behaviours from the fixed list. Publish a benchmark-style results page like race 1's, with charts per question. Stop at the gate.
6. At the end, write the deliverables the charter lists: the final benchmark report, model and method profiles, the Working with Claude Code guide, and the winning checklist as a reviewed change.

Rules that never bend:
- Never change grounded-class-tutor or the owner's checkout of it; read only. Never merge. Never add or remove owner-ok.
- One sandbox per run. Hidden tests and the answer key stay out of every run's reach; discard any run that read them.
- Respect the per-run ceilings and stage budgets. Halt and report at 80% of a stage budget.
- Decision rules are fixed before stage 1 and never changed after seeing a result. If you find a flaw mid-stage, log it and report it; don't patch it silently.
- "Done" means verified by a script or by CI. Tag every claim with who checked it: Script, CI, Judge, Run says, or Not checked. A profile claim needs at least 3 observations and shows its count.
- Keep proportion. Rank every risk and finding by how much it moves the goal: trustworthy PRs for little owner attention. Put small risks in one line and move on; never let them steer the design or the owner's attention.
- The owner reads pages, not chat: one or two lines in chat plus the link. Plain words, real examples, clear trade-offs.
```

## What already exists

Race 1 left a working kit. The orchestrator reuses it rather than starting over.

| Thing | Where | Use in race 2 |
| --- | --- | --- |
| Race design and run log | `~/repos/pipeline-bench/SPEC.md`, `runs/ROSTER.md` | Starting point, with its lessons |
| Shapes A and B, reviewer briefs, sandbox scripts | `~/repos/pipeline-bench/shapes/` | Become arms P2 and P3 once the race 1 fixes go in |
| Scoring script | `~/repos/pipeline-bench/grader/grade.py`, `score.sh` | Extend to the new tickets and repos |
| Stand-in owner answer sheet | `~/repos/pipeline-bench/answers/owner.md` | Replace with the single policy for all arms |
| Practice app | private repo `Natenc12/pipeline-lab` | Smoke test for harness changes |
| Today's real checklist and its tools | `~/.claude/skills/work-ticket/` | Source for arm P2. The guard hook protects your checkout |
| Race 1 results | [benchmark page](https://claude.ai/artifact/Qct9n8wauKwo6GzRx5NnnJ) | Baseline, and the template for result pages |
| How race 1 came about | [verdict](https://claude.ai/artifact/AVhinks6xrZRBJv2W9H88U), [pipeline shape](https://claude.ai/artifact/56oKpfxBWyqUKJo6SVT6ui), [race plan](https://claude.ai/artifact/Dnn63kYy2yWMNvfmEScPop) | Background |

## Your decisions

Decided in chat on Nov 21, 2026. The orchestrator follows these.

| Question | Decision |
| --- | --- |
| Budget for stage 1 | Full stage 1: all 72 runs (process arms plus spec levels) at once, about 14–22M tokens, plus about 1–2M for the judge |
| Who plays you during runs | A separate judge agent. It sees only the run's question, with the arm's name removed, and picks the matching reply from the frozen sheet. The orchestrator pastes it |
| Which GCT commit to freeze | Today's `main` |
| Other codebases for stage 4 | The research agent shortlists 3 to 5, and you pick 1 or 2 |
| Where the winner goes | After stage 3, it replaces `work-ticket` through a normal reviewed pull request, with the race results linked |
