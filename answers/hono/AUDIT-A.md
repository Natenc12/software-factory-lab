# Hono tickets T1, T2, T3, T7: independent audit (auditor A)

Audited at tickets commit `8db81df` (branch `claude/hono-tickets`, pull request 59) against a private
clone of the local practice repository (read only; never pushed). Bases: T1 `0cc562d`, T2 `2224731`,
T3 `ae300f5`, T7 `e4a7925`. Tags: Script (I ran it), Read (I read it), Not checked. Evidence per
ticket is in `T<n>/audit.md`. "Real grader" is `grader.grade.grade_commit` with
`grader/codebases/hono.json` and the ticket's own key: 25 grades in all. I built all four fixes blind
before opening `answers/` or the pull request's description.

## Verdicts

| Ticket | Kind | Verdict | My blind fix, real grader | Worst finding |
|---|---|---|---|---|
| T1 | replay (router) | PASS WITH FIXES | hidden 6/6, no trap, `script_pass=True` | a fix that keeps the first value only before the last segment passes 6/6 |
| T2 | replay (auth middleware) | PASS | hidden 4/4, no trap, `script_pass=True` (same regex as the reference) | none that changes a grade; nearly every run will pass |
| T3 | replay (Bun adapter) | PASS WITH FIXES | hidden 2/2, no trap, `script_pass=True` | leaving the in-scope `@hono/bun` copy untouched passes 2/2 |
| T7 | vague | PASS WITH FIXES | guessed one label: 3/6, `script_pass=False` (as intended); changed to the owner's answer: 6/6, `script_pass=True` | a pattern with unescaped dots (allows `https://app.examplexcom`) passes 6/6 |

All four references grade `script_pass=True` with no trap, against the frozen hidden tests (author's
`verify.json`, Read) and against the strengthened hidden tests proposed below (Script, real grader).
No ticket fails outright: every must-fix item is an edit to a hidden test, one line of a key, or one
sentence of the tickets.

## Must fix (ranked by how much each would distort results)

1. **T3. A run that never touches the `@hono/bun` copy passes.** Script: the reference with
   `adapters/bun/` restored grades `script_pass=True`, 2/2. The ticket puts the copy in scope and a
   reply confirms it; the key calls it "not graded" because the package's tests need Bun. They do
   not need Bun to be graded: the copy imports only `hono/ws`, which resolves to `dist/` after the
   build the grader already runs. Edit `answers/hono/T3/hidden/t3.test.ts` to load
   `../../adapters/bun/src/websocket` at run time and run the two tests over both copies with
   `describe.each` (exact text in `T3/audit.md`, item 1; a static import breaks the type check with
   the hidden test in place, a run-time import does not). Script: reference 4/4 and
   `script_pass=True` with it; skip-the-copy variant 2/4; my blind fix 4/4; base 0/4.
2. **T7. Two careless matchers pass 6/6.** Script, both `script_pass=True`: (a) the reference
   without `escapeRe`, so `https://*.example.com` allows `https://app.examplexcom`, the look-alike
   hole the ticket exists to close; (b) `*` treated as a wildcard anywhere, so `https://app.*.com`
   matches, which the ticket's Out and a reply forbid. Edit `answers/hono/T7/hidden/t7.test.ts`: add
   `'https://app.examplexcom'` and `'https://app.example-com'` to the cors `refused` list and the
   first to the csrf list; add three `toBeNull()` lines for `corsApp('https://app.*.com')`,
   `corsApp('https://example.*')` and the list form, and one `toBe(403)` line for csrf (exact text
   in `T7/audit.md`, items 1 and 2). Script: reference 6/6 and `script_pass=True` with them; each
   variant then fails two tests; my asked-the-owner build 6/6; base 0/6.
3. **T3. The key traps `src/helper/websocket/`, which the ticket does not put out of scope.**
   Script: my blind fix plus one change, `WSEvents.onError`'s event typed as
   `Event & { error?: unknown }` so an app can read the `error` the ticket promises, grades
   `script_pass=False` on `scope_out_paths`, with hidden 2/2. Edit: remove
   `"src/helper/websocket/"` from `answers/hono/T3/key.json` `scope_out_paths`, or add "The shared
   WebSocket helper (`src/helper/websocket/`) and its types" to the ticket's Out and recount
   `spec_words`.
4. **T1. Keeping the first value only before the last segment passes 6/6.** Script,
   `script_pass=True`: `/:a/:id/:id` on `/1/2/3` still gives `id` = `3`, but every hidden test (and
   every example in the ticket) repeats the *first* name of the path, which an old special case in
   `#pushHandlerSets` already covers. Edit `answers/hono/T1/hidden/t1.test.ts`: add the test "self
   after another parameter" (`/:a/:id/:id` gives `2`; `/:a/:id/:id/x` gives `2`; exact text in
   `T1/audit.md`, item 1). Script: reference 7/7 and `script_pass=True` with it; variant fails it;
   my blind fix 7/7; base 0/7.
5. **All eight tickets. "Done when: `pnpm test` passes" names a command that fails by itself on a
   busy machine.** Script: `vp test --run --project node` on the untouched T7 base, 15 runs while
   my grades ran alongside: 6 failed, each on a "Should call onAbort" test timing out at 5 s. The
   grader rightly leaves that project out; the tickets and the practice repo's workflow do not.
   When several stage runs share a machine, a run doing exactly what the ticket says will sometimes
   see a red suite it did not cause, and can lose tokens chasing it or edit the test (which trips
   `existing_tests_changed`, since `runtime-tests/` is a test folder). I did not observe a run doing
   either; the red suite itself is measured. Edit, in the Notes of each
   `tickets/hono/T*/S1.md` (true of the code at every base, and what an owner would say): "The Node
   adapter's 'Should call onAbort' tests (`runtime-tests/node`) are timing-sensitive and can fail on
   a busy machine; that is known and not part of this ticket." Recount `spec_words`.
6. **T1. Folding `node.test.ts`'s "self" case into a table trips `existing_tests_changed`.**
   Script: the reference with that one existing case and its three new siblings rewritten as an
   `it.each` grades `script_pass=False`. The key already allows the same edit to the shared "self"
   case. Edit `answers/hono/T1/key.json` `tests_may_change`: add
   `"src/router/trie-router/node.test.ts::Duplicate param name > self"`.
7. **T3. Async rejections are checked for `onMessage` only.** Script: a variant that watches the
   returned promise only in `message` grades `script_pass=True`; the ticket says all three handlers.
   Edit: the eleven lines for async `onOpen` and `onClose` in `T3/audit.md`, item 3 (same proposed
   file as item 1; reference and my blind fix pass, the variant fails).

## Worth doing

- T1: `tests_may_change` lists whole files "for skip lists", but a skip-list edit never trips the
  trap anyway (Script); the entries only let a run rewrite any named case in every router's test
  file. Replace them with `"src/router/common.case.test.ts::Common > Duplicate param name > self"`
  and the entry from item 6. Script: with that list the grader's own function passes the reference
  and both blind fixes.
- T1: add `"src/router/pattern-router/router.ts"` to `scope_out_paths`; the ticket's Out names
  PatternRouter and the key does not.
- T1, for the grader's owner: a failing existing shared case can be silenced through a `runTest()`
  skip list with no trap. Script: an `in`-operator fix that breaks "Reserved words and named
  parameter" grades `script_pass=False` (own suite red); the same fix plus one skip entry grades
  `script_pass=True`. Rule to add in the grader, and a per-ticket stopgap, are in `T1/audit.md`,
  item 5. If auditor B's tickets touch routers, the same applies there.
- T2: `basicAuth` and `bearerAuth` escaping only a trailing backslash passes 4/4 (Script,
  `script_pass=True`) because each middleware is tested only with its own example. Add one mixed
  realm (`'a\\b "c"\\'`) to each of the four hidden tests (text in `T2/audit.md`, item 1; reference
  passes, variant fails; Script).
- T3: add `adapters/deno/` and `adapters/cloudflare-workers/` to `scope_out_paths` beside their
  `src/adapter/` twins.
- T7: the key lets six existing tests change while the ticket says "every existing test passes
  unchanged"; make them agree.
- Local practice clone: `~/repos/hono-lab` carries branches `blind/T1` to `blind/T8` (complete
  fixes) and `lab-main`. They are not on GitHub (Script, `gh api`: only `main`, `base/T1..T8` and the
  candidate tags), and a run's checkout is a fresh fetch of one base ref with fetching denied
  (Read, `harness/sandbox.py`), so nothing leaks today. Delete them before the stage anyway.

## The Hono-specific checks I was asked for

- **The graded command and its two exclusions.** Script. Graded command on the untouched bases, 3
  runs each on T1, T2, T3, T7: 12 of 12 green, 15 to 33 s each. Across my 25 real-grader runs (each
  runs the own suite, most of them while a second auditor's suites ran) no own test failed and then
  passed on the re-run, and none failed that the variant under test did not break. The project's plain
  `pnpm test`: 7 of 7 green (3 quiet on T7, 4 under load on T3). The `node` project alone under
  load: 6 of 15 red, always "Should call onAbort" timing out at vitest's 5 s limit (see must-fix
  5), so the exclusion is justified. I did not test whether a 30 s limit alone would rescue them. The raised
  `--testTimeout`: I did not see `build/jsx-types.test.ts` overrun, but it is the one `build/` test
  without its own 30 s limit (Read), so the reasoning holds. Nothing else was unstable.
- **`tests_may_change` against what a careful engineer would extend.** T1: must-fix 6 and the first
  "worth doing" line. T2: right, and proven (Script: my fix with a backslash added to the two listed
  tests grades `script_pass=True`, both under `allowed_by_key`). T3: rightly empty. T7: harmless
  mismatch with the ticket. `check_packages.py hono` passes against my clone (Script).
- **A published `hono` inside `node_modules`.** Script, after the config's install on each of the
  four bases: `node_modules/.pnpm/hono@4.13.9` (peer of the dev dependency `@hono/node-server@2.1.1`),
  the same package on all four; every `adapters/*/node_modules/hono` is a link back to the checkout
  itself. 4.13.9 is older than every base (4.13.13 to 4.13.21) and contains none of the fixes: its
  TrieRouter still assigns `params[name] = part`, all four auth files still escape quotes only, its
  Bun adapter never reads `onError`, and it has no origin patterns. The shared pnpm store the
  grader's install reads holds `hono@4.13.9` and `hono@4.13.2` only (Script, the store's index); a
  sealed run's own store is filled from the same lockfile.
- **Starting points.** Script. Each replay base is the fix's parent plus the setup commit; no fix,
  fix test or pull request number is reachable from any of the four bases.

## Checked and fine

- Every statement I tested in the four tickets is true at its base (T1's router table by a probe of
  four routers; the others by reading the code).
- No reply contradicts its ticket; no stop I could construct matches two replies with different
  outcomes, except "I recommend one label, OK?" on T7, which matches the common `default` too and
  relies on the sheet's "ticket's own reply fits better" rule.
- T7's decision is open at the base, flagged in the ticket, answered in full by the sheet, and the
  obvious guess (one label: the author's blind fix and mine) fails 3/6.
- Lint and format are clean on all four blind fixes and references (Script).
- None of the four tickets names its fix. T1's title and example are close to the public issue's;
  runs have no web access.

## Not checked

- No experiment run and no reply-judge or quality-judge call was made; every reply-sheet statement
  above is from reading.
- Whether the `node` project can open its local sockets at all inside a sealed run's sandbox.
- T3 under a real Bun; `bun test` and `tsc` for the `adapters/bun` package.
- T4, T5, T6, T8 (auditor B), `grader/` code beyond the functions I called, and the harness.
- Token cost and wall time of an agent on these tickets (I did not run one; the author's blind-fix
  table is unverified).
