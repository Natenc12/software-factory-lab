# Tickets

One folder per ticket, per codebase. Everything here and in `answers/` is frozen before stage 1.

## The eight tickets for a codebase

| Id | Kind | What it must catch |
|---|---|---|
| T1, T2, T3 | History replay | Real difficulty with a known right answer: a real bug-fix commit, replayed from the commit before it |
| T4 | Multi-file feature | A feature crossing at least 3 modules |
| T5 | Vague | One decision is left genuinely open; the owner has one fixed answer |
| T6 | Flawed | The request conflicts with a recorded decision or an existing test |
| T7 | Migration on data | A schema change that must keep existing rows intact |
| T8 | Review only | A branch with 3 planted bugs, one visible only when the code runs |

## Ticket package (what a run may see)

```
tickets/<codebase>/<T>/
  S1.md       the standard ticket: Problem / Why / Scope (In, Out) / Decisions / Done when / Notes
  S0.md       the rough capture as first filed, before triage          (not for T8)
  S2.md       S1 plus worked examples, explicit failure cases, a must-not-change list   (not for T8)
  S3.md       S2 plus one line naming the acceptance tests already in the branch        (not for T8)
  meta.json   see below
```

`meta.json`:

```json
{
  "id": "T1", "kind": "replay", "title": "short title",
  "repo": "Natenc12/gct-lab",
  "base_ref": "base/T1",          "s3_base_ref": "base/T1-s3",
  "db": "postgres",
  "deliverable": "pull_request",
  "spec_words": {"S0": 0, "S1": 0, "S2": 0, "S3": 0}
}
```

- `base_ref` is a branch in the practice repo that the run starts from. For a replay it is the commit
  before the real fix. `s3_base_ref` is the same commit plus the acceptance tests, in one extra commit.
- `deliverable` is `pull_request`, or `review_report` for T8 (the run writes `scratch/review.md`).
- `spec_words` counts the words the owner would have to read and approve at each level.
- A ticket text never names the arm, the experiment, hidden tests, or the original fix. No code or
  hints copied from the original pull request. Every fact in it is true of the code at `base_ref`,
  except the planted flaw in T6, which `key.json` names.

## Answer package (never visible to a run)

```
answers/<codebase>/<T>/
  hidden/test_hidden_*.py   hidden tests, written against behaviour the ticket asks for
  reference.patch           a reference fix: `git diff` against base_ref that makes the hidden tests pass
  key.json                  see below
  replies.md                ticket-specific stand-in owner replies, in the reply-sheet format
  audit.md                  the auditor's verdict (written by the auditor, not the author)
```

`key.json`:

```json
{
  "hidden_test_cmd": "uv run pytest -q -m 'not live' tests/hidden",
  "unchanged_paths": ["paths that must be byte-identical to base_ref"],
  "scope_out_paths": ["paths the ticket puts out of scope"],
  "traps": [{"id": "applied-migration-edited", "check": "unchanged_paths", "paths": ["migrations/0001_init.sql"]}],
  "flaw": {"what": "T6 only: the conflict", "evidence": "file or decision record that shows it", "right_outcome": "raise it before building"},
  "open_decision": {"what": "T5 only", "owner_answer": "the one fixed answer", "hidden_tests_assume": "that answer"},
  "planted_bugs": [{"id": 1, "where": "file:line", "what": "", "visible": "diff | edge case | only when run"}],
  "not_bugs": ["T8: things a reviewer may flag that are not defects"]
}
```

Rules for hidden tests: each fails on `base_ref`, passes with `reference.patch`, checks only behaviour
the ticket text asks for (not too wide), and would pass for a different correct fix (not too narrow).
They need no network and no paid API.

`replies.md` uses the harness sheet format (`## <id>`, `When:`, `Reply:`). Ids are prefixed with the
ticket, for example `T5-open-decision`. The common replies live in `answers/reply-sheet-common.md`.
