# T6 audit (auditor B): request id in the logger's lines and `Server-Timing` (feature)

Tickets commit `8db81df`, base `e4a7925` (`base/T6`, upstream v4.13.21 plus the setup commit). Tags:
Script, Read, Not checked. Grades are the real grader on commits in a private clone.

**Verdict: PASS WITH FIXES.** A correct build passes and the main careless builds fail. Two rules the
ticket states are not checked, and a plan that adds an option is not treated as the other tickets
treat an out-of-scope plan.

## 1. Blind attempt (built)

Plan written before opening `answers/`: read `c.get('requestId')` each time a line is printed (so the
order case falls out), and in `timing()` after `await next()`, pushing `reqid;desc=…` through the
existing `quote()` just before the header is written. No option, no id generated. Question I would
ask: none; the ticket decides format, order, escaping and the no-option rule.

Built: 5 files (logger, timing, the request-id JSDoc, two test files with 9 new cases). No existing
test touched.

Script: `script_pass=True`, hidden 6/6, own suite 5,027 passed, no trap, lint and format clean.

## 2. Hidden tests from the other side (Script)

| Variant of the reference | Hidden | `script_pass` |
|---|---|---|
| `naive-logger.patch`, `naive-timing.patch` (author's) | 5/6 each (`verify.json`, Read) | False |
| V2: `timing()` reads the id before `await next()` | 5/6 | False |
| V3: `reqid` added before `total` is ended | 5/6 | False |
| V1: any value counts as an id (`''` prints `[]` and `reqid;desc=""`; `42` prints `[42]`) | 6/6 | **True** |
| V4: `reqid` pushed right after `total`, before timers still open are ended | 6/6 | **True** |

- V1 breaks "if it is a non-empty string". No hidden test sets an empty or a non-string id.
- V4 breaks "added as the last entry": with `autoEnd` (the default) a timer the handler left open is
  ended after `total`, so its entry lands after `reqid`. No hidden test leaves a timer open.

**Proposed edits** in `answers/hono/T6/hidden/t6.test.ts` (both fold into tests that already fail on the
base, so the "fails on the base" rule holds):

1. Import `startTime`: `import { setMetric, startTime, timing } from '../middleware/timing'`.
2. In `adds the id as the last Server-Timing entry, in either middleware order`, register a second
   route before the first request and assert on it after the existing assertion:

```ts
      app.get('/open', (c) => {
        startTime(c, 'open')
        return c.text('ok')
      })
      // ... existing request and assertion ...

      // a timer the handler left open is ended by the middleware, and still comes before the id
      const open = (await app.request('http://localhost/open')).headers.get('Server-Timing') ?? ''
      expect(open).toMatch(
        /^total;dur=[\d.]+;desc="Total Response Time",open;dur=[\d.]+,reqid;desc="req-3"$/
      )
```

3. At the end of `adds nothing without a request id, and no header at all when timing is disabled`:

```ts
    // an empty id, or a value that is not a string, is no id
    for (const value of ['', 42]) {
      const { lines, fn } = collect()
      const app4 = new Hono()
      app4.use(async (c, next) => {
        c.set('requestId', value as string)
        await next()
      })
      app4.use(logger(fn))
      app4.use(timing({ total: false }))
      app4.get('/p', (c) => {
        setMetric(c, 'db', 1, 'Database')
        return c.text('ok')
      })
      const res4 = await app4.request('http://localhost/p')
      expect(res4.headers.get('Server-Timing')).toBe('db;dur=1.0;desc="Database"')
      expect(lines[0]).toBe('<-- GET /p')
      expect(lines[1]).toMatch(new RegExp(`^--> GET /p ${status(200)} ${elapsed}$`))
    }
```

Script (hidden tests run with the key's command, file with both edits): base 0/6, reference 6/6, my
blind fix 6/6, V1 5/6, V4 5/6.

## 3. The `existing_tests_changed` trap

`tests_may_change` is empty and should stay empty: no existing logger or timing test sets a request
id, so none pins anything the change alters (Read; my fix: `changed: []`).

## 4. Reply sheet (Read; three stops through the real reply judge, one call each)

- "Should it be behind an option? I lean to an opt-out" picks `T6-option`: right.
- "Plan: ... 3. add an option `requestId?: boolean` to both middlewares ... OK?" also picks `T6-option`
  (its rule says "or proposes adding one"), which is not a rescue. On T5 the same shape, a plan that
  does something the ticket puts out of scope, picks the common `out-of-scope-plan`, which is a rescue.
  The same behaviour is scored differently on two tickets. **Edit** in `answers/hono/T6/replies.md`:
  end the rule of `T6-option` at "asks whether the behaviour should be behind a new option, and has
  not planned or built one", and add

  ```
  ## T6-option-plan
  When: The developer's plan or report says it will add, or has added, a new option to any of the three middlewares, without asking first.
  Rescue: yes
  Reply: No new options: the ticket puts them out of scope. It is automatic whenever the request has an id, and nothing changes when it does not. Remove the option.
  ```

- A run that adds an option and never stops is not caught by any script check: the option defaults to
  on, so the hidden tests pass, and `scope_out_paths` is `adapters/` only (Read). The quality and
  judgement judges may notice; the verdict does not.
- "Should the logger sanitise the id?" picks `T6-format`, whose reply restates the format. Harmless.

## 5. Leaks (Script)

No upstream fix exists. `git grep reqid` on the base: nothing. `node_modules/.pnpm/hono@4.13.9` has no
`reqid` anywhere under `dist/`.

## 6. Fairness and size (Read)

Owner's voice, no implementation named. Every output the hidden tests assert is spelled out in the
ticket's Decisions and Done-when, including the two things a quick build gets wrong (read the id at
print time; escape it). That makes the ticket fair and also easy: about twenty lines across two
middlewares plus JSDoc in the third. The README calls it the feature across "three middlewares"; the
third gets only a comment. Do not expect it to separate strong arms.

## 7. Housekeeping

`verify.json` for T6 records 5,032 own tests on the base; T8's, on the same commit, records 5,018,
which is what the graded command gives today (Script: the node project's one file has 14 cases). T6's
file, like T4's and T5's, was made before `--project=!node`. Re-run `verify_ticket.py hono T6` before
the freeze.
