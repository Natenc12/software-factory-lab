# Arm P4 Team, revised: one writer, a blind tester, a fresh reviewer

**Tests:** Q4. **This replaces the charter's P4. It does not add an arm.**

## Why change P4

The charter's P4 has five roles, including a separate architect, each seeing only part of the job. The evidence points against that shape:

- Subagents working on slices of one job make clashing hidden decisions. What works is "writes stay single-threaded", with helpers that only read and a clean-context reviewer ([Cognition 2025](https://cognition.com/blog/dont-build-multi-agents), [Cognition 2026](https://cognition.com/blog/multi-agents-working), both read 2026-11-21).
- Across 7 multi-agent frameworks, 41–86.7% of runs failed, often through loops, ignoring the spec, unclear stopping and weak checking. Better role prompts gave only about +9 points ([MAST](https://arxiv.org/html/2503.13657v3), read 2026-11-21).
- Multi-agent setups use about 15× the tokens of a chat, and coding is rarely parallel ([Anthropic](https://www.anthropic.com/engineering/multi-agent-research-system), read 2026-11-21).
- Anthropic kept a planner, because without it the builder under-scoped, and a separate evaluator. It dropped the other structure as models improved ([Anthropic](https://www.anthropic.com/engineering/harness-design-long-running-apps), read 2026-11-21).
- A test writer that never sees the code finds more bugs than the coder testing itself ([AgentCoder](https://arxiv.org/html/2312.13010v3), read 2026-11-21).

So P4 keeps the parts with evidence (planner, blind tester, fresh reviewer) and drops the part without it (a separate architect handing a design note to the builder).

## What the run is given

A lead agent runs four roles, in this order. Each role is a separate subagent with only the inputs listed.

| Role | Sees | Writes | Tools |
| --- | --- | --- | --- |
| Planner | Ticket, code (read-only) | Contract: what must be true, examples, must-not-change list. Also a short design note: which files, which approach | Read only |
| Builder (the only writer of product code) | Ticket, contract, design note, code | The change, plus its own tests | Full sandbox |
| Tester | Ticket and contract only. **Not** the diff, not the builder's tests | Acceptance tests in a separate file, written before seeing the code, then run against the branch | Write only under one tests folder; run tests |
| Reviewer | Ticket, contract, diff, test results. **Not** the planner's or builder's reasoning | Blocking findings and notes | Read only; run tests |

The lead passes files between roles, loops builder → tester/reviewer at most twice, and writes the merge brief. The planner, tester and reviewer are always fresh contexts.

Owner stops: same as the charter's P4. Stop only if the contract is wrong, then the merge brief.

## What changes from the charter's P4

- The architect role merges into the planner (one fewer handoff).
- The tester is explicitly blind to code, and its tests go in their own file, so the grader can see them.
- The builder alone writes product code. No other role edits it.
- A hard loop limit of 2 review rounds, against the "step repetition" and "unaware of when to stop" failures.

## Expected extra cost

About 2–3× P3 per run, based on race 1's P3 runs (about 90–110k tokens) plus three fresh subagents. Per-run ceiling: 3× the stage-1 P4 smoke-run mean. If the smoke runs on `pipeline-lab` exceed 4× P3, report that at the gate before stage 1.

## How we would know it helped

Uses the charter's Q4 test: the team catches more and needs the owner less, at a cost the owner accepts. Concretely, against P3 and P1R:

- More trustworthy PRs (more than one per 8 tickets), or fewer rescues.
- The tester's blind tests fail on the starting code and catch at least one real bug the builder's tests missed, in at least 3 runs. Otherwise the tester adds cost but no evidence.
- Watch the MAST failure tags (see [../failure-modes.md](../failure-modes.md)): loops, lost handoffs, a reviewer ignored by the lead.
