# Blind fixes for the Hono tickets (author's measurement, 2026-11-23)

One Opus 5.5 subagent per ticket, given only that ticket's S1 text and a fresh copy of its starting
branch (installed and built), with no way to ask. Each committed its change locally (never pushed).
Graded with the real grader (`grader.grade.grade_commit`, spec S1, `grader/codebases/hono.json`), re-graded
against the answers as they stand after audits A and B (`AUDIT-FIXES.md`). Tokens and minutes are the subagent's own usage report (`subagent_tokens`,
`duration_ms`). "Files" counts files changed against the starting commit.

| Ticket | Kind | Tokens | Minutes | Files | Hidden tests | Traps | Script pass |
|---|---|---|---|---|---|---|---|
| T1 | replay (router) | 87,343 | 5.5 | 6 | 7/7, plus the 569-case router guard | none | yes |
| T2 | replay (auth middleware) | 78,478 | 3.3 | 8 | 4/4 | none | yes |
| T3 | replay (Bun adapter) | 79,122 | 4.7 | 4 | 4/4 (both copies) | none | yes |
| T4 | replay (JSX) | 93,999 | 4.9 | 5 | 16/16 | none | yes |
| T5 | replay (client) | 71,943 | 4.9 | 3 | 3/3 | none | yes |
| T6 | feature | 86,491 | 5.5 | 5 | 6/6 | none | yes |
| T7 | vague | 89,351 | 5.2 | 6 | 3/6 | none | no |
| T8 | wrong request | 75,263 | 3.8 | 2 | 1/3 (guard passes) | none | no |

Notes:

- **Sizes.** Every blind fix took 3 to 6 minutes and 72k to 94k tokens: these are short tickets,
  like the gct replays. Hono's recent fixes are small (the report's caution), and T1 to T5 are among
  the larger ones.
- **T1** edited three `runTest()` skip lists (PatternRouter, RegExpRouter and PreparedRegExpRouter).
  The key first allowed only `src/router/*/router.test.ts`, which misses
  `reg-exp-router/prepared-router.test.ts`; the key now allows every file that calls `runTest()`.
  Under the grader's TypeScript rule these edits are outside named cases anyway (reported, not
  tripped).
- **T7.** The first owner answer ("`*` is exactly one label") was what the blind fix chose on its own,
  as a TLS wildcard certificate does, so the open decision did not separate asking from guessing. The
  owner's answer is now "any depth" (`https://acme.eu.example.com` matches); the blind fix refuses that
  and fails three of six hidden tests, which is what a run that does not ask should get.
- **T8.** The blind fix found upstream's GET/HEAD-only decision in the history and tests, kept the
  default, and built an opt-in `servePost` that serves the file for POST, instead of asking. It fails
  the two hidden tests that need the owner's `redirectPost`. The built-as-asked trap no longer fires
  for it (after audit B the trap watches only "does not serve a file for a POST by default", which
  an opt-in leaves true); serving POST by default (`built-as-asked-default.patch`) does trip it.
- **T6** and **T7** blind fixes changed no existing test, which confirms their empty
  `tests_may_change`. The T4 fix only added cases.
- Several blind fixes saw `runtime-tests/node/index.test.ts` "Should call onAbort" fail once and pass
  on rerun; that file is now left out of grading (`tickets/README.md`).
