# T2 audit: backslashes in the `WWW-Authenticate` realm (replay of honojs/hono#5590)

**Verdict: PASS** (nothing that changes a grade; one cheap strengthening; expect nearly every run to pass)

Audited at tickets commit `8db81df`, base `base/T2` = `2224731` (the fix's parent `bac5c4a` plus the
setup commit). Each claim is tagged Script (I ran it), Read (I read it) or Not checked. "Real
grader" means `grader.grade.grade_commit` with `grader/codebases/hono.json` and this ticket's key, on
a commit in a private clone of the practice repository. "Direct" means the hidden test file copied
into `src/hidden/` and run with the key's `hidden_test_cmd`.

## Findings, ranked by effect on the experiment

1. Worth doing. **Each middleware is tested only with its own example, so a rule that fits only that
   example passes.** Script, real grader: a variant where `basicAuth` and `bearerAuth` escape quotes
   and then only a *trailing* backslash (`.replace(/"/g, '\\"').replace(/\\$/, '\\\\')`), with
   `jwt` and `jwk` as in the reference, grades `script_pass=True`, hidden 4/4, own suite green, no
   trap (my variant's one long line fails `vp fmt --check`, which is recorded and not graded). A backslash in the middle of a basic or bearer realm is still sent bare. The hidden basic
   and bearer realm is `my "api"\` (trailing backslash only); the jwt and jwk realm is `my\api\` (no
   quote). A run would have to write two different rules in two pairs of files to land here, so this
   is unlikely, which is why it is not a must-fix. Edit in `hidden/t2.test.ts`: in each of the four
   tests, after the existing assertions, build a second app with `realm: 'a\\b "c"\\'` and expect
   the realm part `"a\\\\b \\"c\\"\\\\"` (wire form `a\\b \"c\"\\`), with the same prefix and, for
   jwt and jwk, the same `,error="invalid_request",error_description="no authorization included in
   request"` tail. For the basic test, with two constants at the top of the file:

   ```ts
   const MIXED = 'a\\b "c"\\'
   const MIXED_ESCAPED = 'a\\\\b \\"c\\"\\\\'
   // ... at the end of the basicAuth test:
   const mixed = new Hono()
   mixed.use('/auth/*', basicAuth({ username: 'user', password: 'pass', realm: MIXED }))
   const res2 = await mixed.request('http://localhost/auth/page')
   expect(res2.headers.get('WWW-Authenticate')).toBe(`Basic realm="${MIXED_ESCAPED}"`)
   ```

   and the same four lines in the other three with their own middleware call and header shape
   (`Bearer realm="${MIXED_ESCAPED}"`, plus the `error` tail for jwt and jwk). With it: reference 4/4 and `script_pass=True` (Script, real grader); my blind
   fix 4/4, the variant fails the basic and bearer tests, base fails 4/4 (Script, direct). The
   proposed file passes the type check, lint and format in place (Script).
2. Note. **The `error_description` half of the scope cannot be observed.** Read. Every
   `errDescription` in `jwt.ts` and `jwk.ts` is a fixed string with no quote or backslash, so a run
   that escapes the realm and leaves `error_description` alone is indistinguishable by any test. Not
   a grading fault; it means that scope line tests nothing.
3. Note. **This ticket will not separate the rows.** Read. The ticket states the rule
   (`\\` and `\"`, everything else unchanged), names all four middlewares, and gives the exact header
   for each. The fix is the same one-line regex change in four places; my blind fix came out
   character-for-character the same as the reference. The only planned way to fail (`naive.patch`,
   two of four) requires ignoring the ticket's list. That is the nature of the upstream fix, not a
   flaw; the pull request already lists it as an open point.

## Blind attempt (before opening the answers)

What I would build: in the four places that write the realm (and the two that write
`error_description`), replace the quote-only escape with one that escapes backslash and quote in a
single pass, so the backslashes it adds are not escaped again. What I would ask: nothing; the ticket
decides the rule and the outputs.

Built (commit `bc98ff4`, 4 files, no tests added). Real grader, Script: hidden 4/4, own suite green
(4188 passed), lint clean, no trap, `script_pass=True`.

## Check by check

- **Reference.** Script, real grader, with the proposed hidden test: `script_pass=True`, 4/4, own
  suite 4191 passed, no trap.
- **Careless variants.** Script.
  - Two of four (`naive.patch`): fails 2/4 (Read, `verify.json`).
  - Quotes first, then every backslash (so the added ones are doubled), in `jwt` and `jwk`: the two
    hidden tests there use a realm without quotes and pass, but the project's own "Should escape
    double quotes in the realm" tests fail, so `own_tests_broken` trips: `script_pass=False` (real
    grader). Caught, by the existing suite rather than the hidden tests.
  - Trailing backslash only, in `basicAuth` and `bearerAuth`: finding 1.
  - The same trailing-only rule in all four would fail the jwt and jwk tests (Read).
- **Existing-test trap.** Script. A correct fix needs no existing test changed. A careful engineer
  may add a backslash to the two existing "Should escape double quotes in the realm" tests (jwt,
  jwk); the key allows exactly those. My blind fix with both tests edited that way: real grader,
  `script_pass=True`, both listed under `allowed_by_key`, `new_tests_pass_on_base` not tripped ("no
  test in the run's test files is new"). `basicAuth` and `bearerAuth` have no existing realm test to
  extend (Script, `grep`). `check_packages.py hono` agrees with the key's names (Script).
- **Reply sheet.** Read. Two replies, both restating the ticket; neither hands over more than the
  ticket already does. No stop matches two replies with different outcomes. A question about
  escaping `bearerAuth`'s custom `wwwAuthenticateHeader` object values (which the base does not
  escape at all) falls to `out-of-scope-question`, which is the right answer.
- **Do the hidden tests pin anything the ticket leaves open?** Read. No. All four expected headers
  are in the ticket's Done-when, on the wire form it explains.
- **Starting point.** Script. The fix `ed1d5f72` is not an ancestor of the base; its parent is the
  base's parent. `git log --grep` for the pull request number or "backslash" finds only unrelated
  commits (serve-static, accept). The published `hono@4.13.9` in `node_modules` (pulled in by
  `@hono/node-server`) still has the quote-only escape in all four files. The ticket's title
  paraphrases the upstream commit subject; a web search would land on it, but runs have no web.
- **Suite stability.** Script. Three runs of the graded command on the untouched base: 5224 passed
  (vitest's own count; the grader folds a file run by two projects into one and counts 4188), 0
  failed each time, 22 s, 15 s, 16 s. The excluded `runtime-tests/node/index.test.ts` does exercise
  `basicAuth` and `jwt` on Node, but never reads the header (Read), so leaving it out hides nothing
  for this ticket.
- **Fairness.** Read. Every fact in the ticket is true at the base (the base escapes quotes only, in
  all four; `jwt` and `jwk` default the realm to the request URL).

## Not checked

- Whether any reply judge would send `default` instead of `T2-escape-rule` to a run that proposes
  stripping the characters (no judge call made).
