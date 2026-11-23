# T5 audit (auditor B): client and per-request `init.signal` (replay of honojs/hono#5650)

Tickets commit `8db81df`, base `615362c` (`base/T5`, upstream v4.13.19 plus the setup commit). Tags:
Script, Read, Not checked. Grades are the real grader on commits in a private clone.

**Verdict: PASS WITH FIXES.** The ticket is fair and a correct fix passes. The two hidden tests can be
passed by two careless fixes.

## 1. Blind attempt (built)

Plan written before opening `answers/`: `deepMerge` recurses into anything `typeof 'object'`, and
spreading an `AbortSignal` gives a plain object. Recurse only when both values are plain objects
(prototype `Object.prototype` or `null`); otherwise the request's value replaces. Question I would ask:
"client value an instance, request value a plain object: replace or merge?" (the ticket decides only
the case where the request's value is not plain).

Built: an `isPlainObject` helper used in `deepMerge`, one unit test in `utils.test.ts`, two client
tests in `client.test.ts`. No existing test touched.

Script: `script_pass=True`, hidden 2/2, own suite 4,991 passed, no trap, lint and format clean.

## 2. Hidden tests from the other side (Script)

| Variant of the reference | Hidden | Own suite | `script_pass` |
|---|---|---|---|
| `naive.patch` (key `signal` special-cased; author's) | 1/2 (`verify.json`, Read) | passes | False |
| V1: keys `signal` **and** `dispatcher` special-cased in `deepMerge` | 2/2 | passes | **True** |
| V2: `init` merged one level deep in `client.ts` (`{ ...options.init, ...reqOptions.init }`), `deepMerge` untouched | 2/2 | passes | **True** |

- V1 handles exactly the two examples the ticket names. The hidden test for "any class instance" uses
  the key `dispatcher`, the ticket's own example, so it cannot tell a general fix from a list of keys.
- V2 breaks the ticket's third decision ("plain-object values and other keys keep merging as today"):
  a plain object under the same key at both levels is no longer merged. No hidden or existing test has
  a nested plain object inside `init` at both levels.

**Proposed edit**: add a third test to `answers/hono/T5/hidden/t5.test.ts`, inside the existing `describe`:

```ts
  it('passes an instance under any key through, and still merges plain objects key by key', async () => {
    class Agent {
      constructor(public name: string) {}
    }
    const clientAgent = new Agent('client')
    const requestAgent = new Agent('request')
    let received: Record<string, unknown> | undefined
    const client = hc<any>('http://localhost', {
      init: { agent: clientAgent, cf: { cacheTtl: 5 } } as RequestInit,
      fetch: async (_input: RequestInfo | URL, init?: RequestInit) => {
        received = init as Record<string, unknown>
        return new Response('ok')
      },
    })

    await client.items.$get(undefined, {
      init: { agent: requestAgent, cf: { cacheEverything: true } } as RequestInit,
    })
    expect(received?.agent).toBe(requestAgent)
    expect(received?.cf).toEqual({ cacheTtl: 5, cacheEverything: true })

    await client.items.$get(undefined, { init: { cache: 'no-store' } })
    expect(received?.agent).toBe(clientAgent)
    expect(received?.cf).toEqual({ cacheTtl: 5 })
  })
```

Script (hidden tests run with the key's command, file with this test added): base 0/3, reference 3/3,
my blind fix 3/3, V1 2/3, V2 2/3. `agent` is not named in the ticket; `cf` is a plain-object value that
merges on the base today.

## 3. The `existing_tests_changed` trap

A correct fix needs no existing test changed (mine: `changed: []`). The key allows the two existing
`deepMerge` cases in `utils.test.ts`, which is where an engineer would extend; nothing else in the
client tests pins the old behaviour (Read). Fine.

## 4. Reply sheet (Read; two stops through the real reply judge, one call each)

- "Plan: combine the two signals with `AbortSignal.any`" picks `out-of-scope-plan` (rescue). Consistent
  with the ticket, which puts combining out of scope in so many words.
- "Client value an instance, request value plain: replace? I recommend yes" picks `default`. Either
  answer passes the hidden tests. Fine.
- No reply contradicts the ticket; `T5-other-instances` repeats a decision the ticket already states.

## 5. Leaks (Script)

- `a46d6025` (the fix) is not an ancestor of `base/T5`; its parent is `676c8f80`, the commit under the
  setup commit. `git grep` on the base for the fix's test names and its `getPrototypeOf(proto)` line:
  nothing. No commit subject on the base mentions #5646 or #5650.
- `node_modules` after install: `hono@4.13.9` only; its `dist/client/utils.js` has the same unfixed
  `isObject` as the base.
- The ticket's example is the upstream issue's reproduction almost line for line (`example.invalid`,
  `client.test.$get`, the two controller names changed). The issue's diagnosis (`isObject`, `deepMerge`
  spreading the signal) is removed. A web search would land on the issue; runs have no web access.

## 6. Fairness and size (Read)

Reads as an owner's report. The override-or-compose choice the issue left open is decided in the
ticket. Every claim checked against the base by my failing tests (Script). A one-function fix of about
ten lines: easy.

## 7. Stability (Script)

The graded command on `base/T5`, three runs: all green, identical results, 14 to 23 seconds each. See
`AUDIT-B.md`.
