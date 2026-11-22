# Skill libraries for coding agents, and two candidate arms

Research for a possible P5 (skills library) and P6 (chief of staff). Everything here was read on
2026-11-22. Tags: **[Read]** means I opened the file myself, at the commit in the Sources list at the
end. **[Says]** means the author claims it and I did not check it. Evidence tied to Claude 4-era models,
or older than about a month, is flagged **weak**.

## The short version

1. **The names all exist.** "pstack" is Lauren Tan's, published in Cursor's plugin repo rather than
   under her own account. "tstack" is Theo Browne's, "gstack" Garry Tan's. [Read]
2. **The best evidence is new, and it is against discretion.** In a November 2026 test on Opus 5.5
   (1,320 sessions on real GitHub bugs, scored by hidden tests), no skill pack fixed measurably more
   than plain Claude Code, and Opus 5.5 mostly ignored the skills: Superpowers started one in 2 of 160 sessions,
   pstack made no skill calls. gstack's own team ran it; gstack did no better (58 of 100 fixed, against
   61 of 99 with no pack). [Read: the result pages; the numbers are Says]
3. **One sentence beat every pack on cost.** "Make the smallest change that fixes the issue, and
   nothing more", added to the task, halved the code at the same fix rate, but also cut new tests (a
   test file changed in 28 of 100 sessions, against 79). [Says, same test]
4. **The libraries agree on checking before claiming,** using output from this session. Most also
   challenge the request; they differ on when to stop for the human.
5. **The harness cannot run skills today.** `--disable-slash-commands` turns off all skills, and
   `Skill` is not in the run's tool list. [Read]

## What each library is

**Superpowers** (Jesse Vincent, MIT). 15 skills: brainstorming, writing-plans, executing-plans,
subagent-driven-development, dispatching-parallel-agents, test-driven-development,
systematic-debugging, requesting-code-review, receiving-code-review, verification-before-completion,
using-git-worktrees, finishing-a-development-branch, writing-skills, diagnosing-superpowers,
using-superpowers. [Read] A start-of-session hook pastes using-superpowers (492 words) into every
session; it says that at "even a 1% chance" a skill applies, the agent must use it. The rest start
from their descriptions (357 words in all). [Read] Brainstorming asks why the work is wanted and gets
a design approved before anything is built. [Read]

**gstack** (Garry Tan, MIT). About 60 skills, mostly slash commands acting as roles: /office-hours
pushes back on how the request is framed; /plan-eng-review and /autoplan review plans; /review, /qa,
/verify, /cso (security) and /ship check and open the PR; /careful and /freeze add safety limits.
[Read] Skills average about 3,800 words; /ship pulls in 44,000 more. The descriptions alone are 1,300
words. Review and ship ask the human at fixed points (7 in /review, 15 in /ship). gstack credits
pstack and tstack for some ideas. [Read]

**pstack** (Lauren Tan, MIT, in `cursor/plugins`). 58 skills: 24 one-paragraph "principle" skills
(prove-it-works, fix-root-causes, attack-the-premise, test-behavior-not-implementation and others),
plus workflows such as interrogate (adversarial review by several models), blast-radius, tdd and
swarm. [Read] 57 of the 58 cannot start themselves (`disable-model-invocation: true`). All run
through one command, /poteto-mode (1,719 words), which picks one of 22 playbooks (7,926 words in all)
and reads principle files by path as steps need them. [Read] Its rules: restate the goal and the
smallest change first; "no is an acceptable answer"; never block on the human for reversible work,
always pause before irreversible work. Code goes to Opus 5.5; Fable 5.2 runs only on review panels
or after two Opus attempts fail. [Read] Her own repos (`how`, `noodle`, `brainmaxxing`, February to
July 2026) are earlier, smaller versions. Unrelated repos also use the name "pstack". [Read]

**tstack** (Theo Browne, MIT). 9 skills, all about the pull-request lifecycle: full-send, full-stop,
council, sol-loop, file-pr, takeover, babysit-pr, modernize, leaving-pr-comments. [Read] Most start
on an exact phrase ("full send"). Full-send defines proof as evidence seen in this session, ideally
"reproduce the failure, fix, watch it pass". It merges with nobody watching. Full-stop stops when the
PR is ready to merge. [Read] Council and sol-loop need models from other companies; babysit needs
`gh`. Neither is possible in our sandbox. [Read]

**Kun Chen** (`kunchenguid`). His `/kun` skill (197 words, no licence file) downloads a script from
the internet, then loads about 25,000 words of his opinions. [Read] It cannot run in our clean room,
and should not: it runs downloaded code. More useful are `no-mistakes`, a push gate that runs review,
tests, docs, lint and CI and hands any finding about intent to the human, and `firstmate` (see P6).
[Read] He reports that on the DeepSWE benchmark, banning Sonnet 5.5 from writing tests slightly
raised success (not significant) and cut time and tokens (significant). [Says; October 2026, another
model, **weak**]

**Anthropic's documentation.** A skill loads in three layers: name and description always (about 100
tokens each); the body when triggered (under 5,000 tokens advised); extra files only when read. The
model matches requests against the description alone, cut at 1,536 characters; the whole list gets
1% of the context window. `disable-model-invocation` hides a skill from the model; a subagent's
`skills:` field pastes chosen skills into it in full. The authoring guide says to write test cases
before the skill. [Read]

## Comparison

| | Superpowers | gstack | pstack | tstack | /kun |
|---|---|---|---|---|---|
| Skills | 15 | ~60 | 58 | 9 | 1 |
| How one starts | Hook forces the index; others by description | Slash command; descriptions; a CLAUDE.md section | Only /poteto-mode, which reads files by path | Exact phrase or description | /kun |
| Words up front | ~850 | ~1,300 plus CLAUDE.md | ~40 | ~110 | ~20 |
| Words on demand | 425–2,985 a skill | 2,000–12,000 a skill | 1,719 plus a playbook plus leaves | 250–930 | ~25,000 downloaded |
| Plan / tests first / debug | yes / strict TDD / yes | yes / no TDD skill / yes | yes / only when asked or cheap / yes | no / no / no | opinions only |
| Review / check before claiming | yes / yes | yes / yes | multi-model / yes | multi-model / yes | opinions only |
| Questions the request | asks why, before building | /office-hours | restate goal; attack the premise | no | no |
| Stops for human | design sign-off | fixed question points | irreversible actions only | full-stop at merge | none |
| Outside evidence (Opus 5.5, Nov 2026) | skill started in 2 of 160 sessions; no gain | -4 points (-11 to +2); dearer per fix | 0 skill calls; no gain | ran 84% of the time; no gain shown | none |
| Licence | MIT | MIT | MIT | MIT | none |

## What they share, and where they differ

**Shared.** Prove it with real output, have a second agent review, keep the change small, say what
you did not check. [Read] All except gstack keep the always-loaded part short.

**Different.** (a) *Who starts a skill.* Superpowers forces itself in with a hook; pstack takes the
choice from the model entirely; gstack and tstack expect the human to type a command. None trusts the
model to choose, and the November test suggests they are right. (b) *Tests.* Superpowers demands
tests first; pstack uses them only when cheap or asked; Kun doubts agent-written tests. (c)
*Stopping.* Superpowers stops early for design approval; pstack never blocks on reversible work;
full-send never stops. (d) *Size.* All of tstack is smaller than one gstack skill.

## How this fits stage 1

Stage 1 points to two things that matter. Checking before claiming: the bare arm's misses were
mostly false claims in its report. Questioning a wrong request: no arm raised the T6 conflict before
building. Heavier fixed process cost 1.6 to 7 times the tokens, asked the owner more, and won
nothing. [Read: `results/stage-1/RESULTS.md` and its page]

On-demand skills are the right shape on cost: a skill costs about 100 tokens until used. The weak
point is the trigger. If Opus 5.5 rarely picks a skill, P5 is just P1 plus a list. The November
test had no wrong asks and no report to grade, so it says nothing about our two failure modes; P5
would.

I recommend a P5 that leaves the *how* to the agent but ties two skills' *when* to moments every
run reaches: after reading the ticket, and before writing the PR. Two lines in the guide do it, far
lighter than P2's checklist. A pure-discretion version is the faithful test of the owner's idea; I
expect it to tie P1. **The owner's call:** pure, pointed, or both.

## Draft arm P5: Skills library

**What a run gets.** P1's `GUIDE.md` (145 words) plus two lines: "Skills are available. Use
check-the-ask after you read the ticket and the code it touches, and prove-each-claim before you
write the pull request." (The pure version leaves them out.) Then six skills. About 300 words load up
front (guide and descriptions); the bodies, about 400 words, load only when used. Drafts, written
fresh, are in the appendix:

| Skill | Starts when | Aims at |
|---|---|---|
| check-the-ask | ticket read, before planning; or the ticket seems to conflict with code, tests, docs or a recorded decision | T6-type wrong asks |
| prove-each-claim | before the PR description or any "passes", "fails" or "tested" line | false claims |
| test-that-bites | adding or changing tests | tests that never failed |
| find-the-cause | a bug ticket, an unexpected failure, or a second failed fix | guesswork fixes |
| stay-in-scope | about to touch files, tests or config the ticket did not name | traps |
| fresh-eyes-review | the change is ready, before opening the PR | missed defects |

**What the harness would need** (from `harness/README.md`, `harness/run.py`, `arms/README.md`):

1. Drop `--disable-slash-commands` for P5 (it turns off all skills), and set
   `disableBundledSkills: true` so Claude Code's own skills (/verify, /code-review) stay out.
2. Add `Skill` to the tool list (`sandbox.ALLOWED_TOOLS` lacks it).
3. Ship the skills as a plugin folder in the control folder, passed with `--plugin-dir`. A project
   `.claude/skills/` would not load under `--setting-sources ""` and would land in the PR's diff.
   [Read: the docs say project and `--add-dir` skills need the project setting source]
4. One file per skill: the guard blocks reads outside the run folder.
5. Teach `arms/README.md`, `SIZES.md` and `tests/test_arms.py` about `skills/*/SKILL.md`, counting
   descriptions as up front and bodies as on demand.
6. Record skill use: count `Skill` calls into a `skills_used` field in `run.json`. Without it, a tie
   with P1 cannot be read.
7. Trial it cheaply first, as in `harness/TRIALS.md`.

## Sketch arm P6: Chief of staff

**Shape.** The main session runs on Fable 5.2. It gets the P1 guide plus a short lead brief: you
answer to the owner (STOP lines, the harness's existing channel); you may do the ticket yourself or
start Opus 5.5 workers, as many as you judge, for whatever parts you choose; you own every claim
in the PR, so read the diff and re-run the checks yourself before reporting. One agent definition,
`worker`, with `model: claude-opus-5-5` and no role. Agent teams do not start under `claude -p`, so
workers are subagents. Fable 5.2 needs CLI 2.1.321 or later. [Read: `research/harness-facts.md`]

**Published guidance.** Kun Chen's firstmate: one lead the human talks to, each worker in its own
worktree, the lead never edits the project and raises only real decisions. [Read, November 2026]
gstack's /captain: workers report "ready" and never merge; the lead merges. [Read] pstack: the lead
owns every worker's output, reviews the diff and writes its own summary, with a fresh worker per
task. It puts Opus 5.5 at the centre and calls Fable 5.2 only when Opus fails, the reverse of P6.
[Read] Anthropic: agent teams cost much more and suit independent work; subagents are cheaper.
[Read] Anthropic's 2025 post found a lead with workers beat one agent by 90% on research tasks, at
about 15 times the tokens. [Says; Opus 4 and Sonnet 4, **weak**]

**How it differs from P4.** P4 fixes five roles, their order and their information barriers, and
bars the lead from writing code. P6 fixes nothing: the lead may work alone or use several workers.
P4 used one model; P6 splits them. P4 cost seven times P1 for no gain, so P6 must show where its
extra money goes.

**Measuring it fairly.**

- Same tickets, same four checks, including the two new wrong-ask tickets planned for stage 2. A
  chief of staff's claimed strength is talking to the owner.
- Two controls, or the result cannot be read: P1 on Opus 5.5 and P1 on Fable 5.2. Otherwise a win
  could be the model, not the coordination.
- Cost in dollars at list price, split by model, not only tokens, since Fable costs more per token.
- Owner words read and stops per ticket, and whether each stop was needed.
- What the lead chose: how often it delegated, how many workers, and whether it checked their claims
  (the false-claim check covers the result).
- At least three runs per cell. A lead's free choices add spread.

## What I could not check

- Whether `--plugin-dir` skills load under this harness's clean room, sandbox and guard, and whether
  `disableBundledSkills` also hides built-in commands. Both need a trial.
- The November test's session records; I read only its two result pages. It was run by gstack's own
  team, scored only on hidden tests (no report honesty, no wrong asks), and had no Python tasks.
- Superpowers' own tests beyond its release notes, which name Sonnet 5 for one test and no model for
  the others. pstack publishes no outcome numbers that I found.
- Theo Browne's other repos, beyond his repo list showing tstack as his only skills repo.
- Kun Chen's benchmark itself; I read only his posts about it.

## Appendix: the six P5 skills (drafts)

Each would be `skills/<name>/SKILL.md` with `name` and `description` in its front matter.

**check-the-ask.** *Description:* Use right after reading the ticket and the code it touches, before
planning or changing anything, and whenever the ticket seems to clash with the code, its tests, its
docs or a recorded decision. *Body:* Write down in one line each what the ticket asks for. Search for
rules that touch it: decision records, docs, comments, tests that pin current behaviour, config
limits. For each rule the ticket would break, note the file and line. If one breaks, do not build
either version yet. Write the owner a short page: what the ticket asks, what it conflicts with (with
the example), and the reading you recommend. Then stop and ask. If nothing breaks, say in one line
that you checked, and where.

**prove-each-claim.** *Description:* Use before writing a pull request description or any report
line that says something passes, fails, works, was tested or was checked. *Body:* List every claim
you are about to make. Next to each, put the command you ran in this session and what it printed. A
claim about the old code ("these tests fail without my change") needs a run on the starting commit,
not a guess. Take numbers from tool output, not memory. Drop or soften any claim you cannot back:
"not checked" is better than a wrong "checked". Then write the description: what was wrong, what you
changed, how you tested it (commands), what you did not check.

**test-that-bites.** *Description:* Use when adding or changing tests for a change. *Body:* Test what
a user of the code can see, not its insides. Run each new test on the starting commit and confirm it
fails for the reason you expect, then confirm it passes on your change. Keep a list of which tests
you checked that way. Do not edit or delete existing tests unless the ticket asks. If an old test
blocks you, that is a question for the owner.

**find-the-cause.** *Description:* Use on a bug ticket, when a test fails unexpectedly, or after a
fix attempt has failed. *Body:* Reproduce the problem first and keep the command. Read the whole
error. Change one thing at a time and re-run. Fix the first place things go wrong, not the symptom.
After two failed fixes built on the same idea, write the idea down and test it directly before
trying a third.

**stay-in-scope.** *Description:* Use when about to change a file, test, setting, migration or
interface the ticket did not mention, or when tempted to tidy or improve nearby code. *Body:* Make
the smallest change that does what the ticket asks. If something outside it truly must change, say
why in the PR. Put good ideas you did not do under "Not done" in the PR instead of doing them.

**fresh-eyes-review.** *Description:* Use when the change is ready and before opening the pull
request. *Body:* Start one subagent. Give it only the ticket, the command that shows your diff
against the starting commit, and how to run the tests. Ask it to find defects, missed cases, scope
creep and any claim in your draft description that the evidence does not support. Judge each finding
yourself. Fix the real ones and re-run the tests. Do not paste your reasoning into its brief.

## Sources (all read 2026-11-22)

- Superpowers: <https://github.com/obra/superpowers/tree/22f0b46> (v7.0.2, `RELEASE-NOTES.md`,
  `hooks/session-start`, `skills/`)
- gstack: <https://github.com/garrytan/gstack/tree/45e33b5> (`README.md`, `NOTICE.md`, `skills`)
- November 2026 skill-pack test, by gstack's team:
  <https://github.com/garrytan/gstack-evals/blob/main/wiki/board/2026-11-19-geva-540-skill-pack-h2h-results/README.md>
  and its correction
  <https://github.com/garrytan/gstack-evals/blob/main/wiki/board/2026-11-20-geva-565-skill-pack-h2h-correction/README.md>
- pstack: <https://github.com/cursor/plugins/tree/7a58391/pstack> (v0.15.46); Lauren Tan's own repos
  <https://github.com/poteto/how>, `/noodle`, `/brainmaxxing`, `/verification-skill-example`
- tstack: <https://github.com/t3dotgg/tstack/tree/11e37a7>
- Kun Chen: <https://github.com/kunchenguid/kun/tree/0e615b9> (`OPINIONS.md`, `content/`),
  <https://github.com/kunchenguid/firstmate/tree/427056c>,
  <https://github.com/kunchenguid/no-mistakes/tree/6d47b8f>
- Anthropic: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview>,
  `.../agent-skills/best-practices`, <https://code.claude.com/docs/en/skills>,
  <https://code.claude.com/docs/en/sub-agents>, <https://code.claude.com/docs/en/agent-teams>,
  <https://code.claude.com/docs/en/cli-reference>,
  <https://www.anthropic.com/engineering/multi-agent-research-system> (June 2025)
- This repo: `results/stage-1/RESULTS.md` and its page, `harness/README.md`, `harness/run.py`,
  `harness/sandbox.py`, `arms/README.md`, `arms/P1`, `arms/P4`, `research/harness-facts.md`
