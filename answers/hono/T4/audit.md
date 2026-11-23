# T4 audit (auditor B): async components returning `null`, a boolean or a number (replay of honojs/hono#5594)

Tickets commit `8db81df`, base `e589c04` (`base/T4`, upstream v4.13.18 plus the setup commit). Tags:
Script, Read, Not checked. Grades are the real grader on commits in a private clone.

**Verdict: PASS WITH FIXES.** A correct fix passes. A correct fix that extends the existing test named
after exactly these values is failed by the test-change trap, and the type change the ticket asks for
is not checked.

## 1. Blind attempt (built)

Plan written before opening `answers/`: every failing path (async component, `html` tag, `Suspense`)
ends in `stringBufferToString`, which assumes each resolved entry is a string. Skip `null`, `undefined`
and booleans there and append numbers, as the sync paths already do; let the component type's promise
resolve to `null`. Question I would ask: "the sync type allows `null` only; widen just the async type
to `null`, or both to every value a child can be?"

Built: `src/utils/html.ts` (the skip and the number case), `src/jsx/base.ts` (`null` inside the promise
of the component type), 16 new test cases in three test files. No existing test touched.

Script: `script_pass=True`, hidden 15/15, own suite 4,931 passed, no trap, lint and format clean. My
type choice (`null` only) differs from the reference (everything a child can be) and passes, because
nothing checks the type; see 3.

## 2. The `existing_tests_changed` trap: a correct fix can trip it (Script)

`src/jsx/index.test.tsx` already has, under `render to string > FC`, a block named `Booleans, Null,
and Undefined Are Ignored` with `it.each([true, false, undefined, null])('%s', …)` for a sync component.
V8 is my passing fix plus two lines added to that case so it also renders the async component:

| Commit | Hidden | Traps | `script_pass` |
|---|---|---|---|
| V8, key as it is | 15/15 | `existing_tests_changed` (`… > FC > Booleans, Null, and Undefined Are Ignored > %s modified`) | **False** |
| V8, key with the two entries below | 16/16 (with the type test of 3) | none | True |

The key already allows the same block in the `html` helper's test file "as the natural place to add
promise-of-value rows". The JSX file has the same block twice (for children and for components) and
neither is allowed. **Edit** in `answers/hono/T4/key.json`, `tests_may_change`: add

```
"src/jsx/index.test.tsx::render to string > FC > Booleans, Null, and Undefined Are Ignored > *",
"src/jsx/index.test.tsx::render to string > Booleans, Null, and Undefined Are Ignored > *"
```

## 3. Hidden tests from the other side (Script)

| Variant | Hidden | `script_pass` |
|---|---|---|
| `naive.patch` (numbers not handled; author's) | 10/15 (`verify.json`, Read) | False |
| V2: fix only in `resolveFunctionComponentResult`, `html` tag left broken | 9/15 | False |
| V1: my fix with the component type left exactly as on the base | 15/15 | **True** |

A differently built correct fix also passes: V9 leaves `stringBufferToString` alone and turns each
value into text where its promise enters the buffer (in the component path and in the `html` tag).
Script: 15/15 with the key's hidden-test command, own JSX, `html` and utils tests green (hidden tests
run directly, not a full grade). So the hidden tests are not tied to the reference's structure.

V1 drops a requirement the ticket states twice ("TypeScript also refuses `async () => null` as a
component today"; Scope: "The component type, so an async component may return what a sync one may").
The hidden tests run under vitest alone, which strips types, so no hidden test can see it.

**Proposed edit**: add `answers/hono/T4/hidden/t4-types.test.tsx`, which type-checks four lines against
the built declarations the way the repository's own `build/jsx-types.test.ts` does:

```ts
import { spawnSync } from 'node:child_process'
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const compiler = createRequire(import.meta.url).resolve('typescript/bin/tsc')
const here = dirname(fileURLToPath(import.meta.url))

describe('component type', () => {
  it('accepts an async component that returns null, as it accepts a sync one', () => {
    const dir = mkdtempSync(join(here, 't4-types-'))
    try {
      writeFileSync(
        join(dir, 'case.tsx'),
        [
          'const Sync = () => null',
          'const Async = async () => null',
          'const Maybe = async ({ show }: { show: boolean }) => (show ? <p>hi</p> : null)',
          'export const page = (',
          '  <div>',
          '    <Sync />',
          '    <Async />',
          '    <Maybe show={false} />',
          '  </div>',
          ')',
          '',
        ].join('\n')
      )
      writeFileSync(
        join(dir, 'tsconfig.json'),
        JSON.stringify({
          compilerOptions: {
            jsx: 'react-jsx',
            jsxImportSource: 'hono/jsx',
            lib: ['DOM', 'ES2024'],
            module: 'NodeNext',
            moduleResolution: 'NodeNext',
            noEmit: true,
            skipLibCheck: true,
            strict: true,
            types: [],
          },
          include: ['case.tsx'],
        })
      )
      const result = spawnSync(
        process.execPath,
        [compiler, '--project', join(dir, 'tsconfig.json')],
        {
          encoding: 'utf8',
        }
      )
      expect(result.stdout + result.stderr).toBe('')
      expect(result.status).toBe(0)
    } finally {
      rmSync(dir, { recursive: true, force: true })
    }
  }, 60000)
})
```

It asserts only `null`, the one value the ticket names for the type, so both the narrow reading (mine)
and the reference's wide one pass. It needs `dist/`, which the grader's build step makes. Script: alone
with the key's command it fails on the base (`TS2786: 'Async' cannot be used as a JSX component`) and
on V1, and passes on the reference and on my fix, in about one second. Under the real grader with this
file added: reference 16/16 `script_pass=True`; V1 15/16 `script_pass=False`.

If the author would rather not add a test that spawns `tsc`, the other fix is to take the type out of
the ticket (the sentence in Problem and the second Scope bullet), since nothing then asks for it.

## 4. Reply sheet (Read; two stops through the real reply judge, one call each)

- "Widen only the async type to `null`, or both to everything a child can be? I recommend both" picks
  `default`. Either choice passes, with or without the type test above. Fine.
- "Plan: ... make the same change in `src/jsx/dom`" picks `T4-dom-renderer`, not the common
  `out-of-scope-plan`, so a plan to change an out-of-scope folder is not a rescue here while the same
  shape is a rescue on T5. The reply itself is right ("No, leave `src/jsx/dom/` as it is"), and the
  `scope_out_paths` trap catches a run that goes ahead. **Edit** in `answers/hono/T4/replies.md`: begin
  the rule of `T4-dom-renderer` with "The developer asks, and has not planned or made the change,
  whether …" so the plan falls to `out-of-scope-plan`.

## 5. Leaks (Script)

- `6e8fbe18` (the fix) is not an ancestor of `base/T4`; its parent `f6fbaf02` is the commit under the
  setup commit. `git grep` on the base for the fix's type name and test names: nothing. No commit
  subject on the base mentions #5575 or #5594.
- `node_modules` after install: `hono@4.13.9` only. Its `dist/utils/html.js` has the same unfixed
  `stringBufferToString`, and its `dist/types/jsx/base.d.ts` has the narrow component type.
- The ticket's example is the upstream issue's reproduction (the `Maybe` component, the same failure
  lines, the same stream tail). The issue's last paragraph, which names the two functions and says the
  sync path already does the right thing, is removed. A web search would land on the issue; runs have
  no web access.

## 6. Fairness and size (Read)

Reads as an owner's report with the expected output for every value. One imprecision: the ticket says
`null` or `undefined` throws "`Cannot read properties of null`"; for `undefined` the message says
"of undefined". Harmless. The hidden streaming test asserts the exact two chunks; that is today's format
for every other value, so a different correct fix produces it too (mine did). A two-file fix of about
ten lines once the common path is found: easy to medium.
