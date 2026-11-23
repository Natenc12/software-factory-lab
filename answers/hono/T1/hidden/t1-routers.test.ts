import { LinearRouter } from '../router/linear-router'
import { PatternRouter } from '../router/pattern-router'
import { RegExpRouter } from '../router/reg-exp-router'
import {
  PreparedRegExpRouter,
  buildInitParams,
  serializeInitParams,
} from '../router/reg-exp-router/prepared-router'
import { SmartRouter } from '../router/smart-router'
import { TrieRouter } from '../router/trie-router'
// Hidden guard for T1 (audit A): every router runs the starting branch's shared cases with the starting
// branch's skip lists, copied here, so a run that silences a broken case by adding it to a skip list
// fails. These tests pass on the base (key.json hidden_tests_may_pass_on_base).
import { runTest } from './t1-common-cases'

describe('RegExpRouter, with the starting skip lists', () => {
  runTest({
    skip: [
      {
        reason: 'UnsupportedPath',
        tests: [
          'Duplicate param name > parent',
          'Duplicate param name > child',
          'Capture Group > Complex capturing group > GET request',
          'Capture complex multiple directories > GET /part1/middle-b/latest',
          'Capture complex multiple directories > GET /part1/middle-b/end-c/latest',
          'Complex > Parameter with {.*} regexp',
        ],
      },
      {
        reason: 'This route can not be added with `:label` to RegExpRouter. This is ambiguous',
        tests: ['Including slashes > GET /js/main.js'],
      },
    ],
    newRouter: () => new RegExpRouter(),
  })
})

describe('PreparedRegExpRouter, with the starting skip lists', () => {
  runTest({
    skip: [
      {
        reason: 'UnsupportedPath',
        tests: [
          'Duplicate param name > parent',
          'Duplicate param name > child',
          'Capture Group > Complex capturing group > GET request',
          'Capture complex multiple directories > GET /part1/middle-b/latest',
          'Capture complex multiple directories > GET /part1/middle-b/end-c/latest',
          'Complex > Parameter with {.*} regexp',
        ],
      },
      {
        reason:
          'This route can not be added with `:label` to PreparedRegExpRouter. This is ambiguous',
        tests: ['Including slashes > GET /js/main.js'],
      },
    ],
    newRouter: <T>() => {
      let router: PreparedRegExpRouter<T>
      const routes: [string, string, T][] = []
      return {
        name: 'PreparedRegExpRouterBuilder',
        add: (method: string, path: string, handler: T) => {
          routes.push([method, path, handler])
        },
        match: (method: string, path: string) => {
          if (!router) {
            const serialized = serializeInitParams(
              buildInitParams({
                paths: routes.map((r) => r[1]),
              })
            )
            const params = eval(serialized) as ConstructorParameters<typeof PreparedRegExpRouter<T>>
            router = new PreparedRegExpRouter<T>(...params)

            for (const route of routes) {
              router.add(...route)
            }
          }
          return router.match(method, path)
        },
      }
    },
  })
})

describe('TrieRouter, with the starting skip lists', () => {
  runTest({
    newRouter: () => new TrieRouter(),
  })
})

describe('LinearRouter, with the starting skip lists', () => {
  runTest({
    skip: [
      {
        reason: 'UnsupportedPath',
        tests: [
          'Multi match > `params` per a handler > GET /entry/123/show',
          'Capture regex pattern has trailing wildcard > GET /foo/bar/file.html',
          'Capture regex param with trailing wildcard on empty remainder > GET /123',
          'Capture regex param with trailing wildcard and sibling route > GET /regex-abc/123/ghi',
          'Trailing wildcard after a label > GET /abc',
          'Trailing wildcard after a label > GET /abc/sub',
          'Trailing wildcard after a pattern label > GET /abc',
          'Trailing wildcard after a pattern label > GET /reverse/abc in reverse registration order',
          'Trailing wildcard after a pattern label > POST /all/abc with ALL middleware',
          'Trailing wildcard after a pattern label > GET /posts/2024/comments with nested braces',
          'Trailing wildcard after a pattern label > GET /files/foo/detail with regexp meta characters',
          'Trailing wildcard after a pattern label > GET /user/123/profile with the default pattern',
          'Trailing wildcard after a pattern label > GET /user/123/profile with the default pattern in reverse registration order',
          'Complex > Parameter with {.*} regexp',
        ],
      },
      {
        reason: 'LinearRouter allows trailing slashes',
        tests: ['Trailing slash > GET /book/'],
      },
    ],
    newRouter: () => new LinearRouter(),
  })
})

describe('PatternRouter, with the starting skip lists', () => {
  runTest({
    skip: [
      {
        reason: 'UnsupportedPath',
        tests: ['Duplicate param name > self'],
      },
      {
        reason: 'PatternRouter allows trailing slashes',
        tests: ['Trailing slash > GET /book/'],
      },
    ],
    newRouter: () => new PatternRouter(),
  })
})

describe('SmartRouter, with the starting skip lists', () => {
  runTest({
    newRouter: () =>
      new SmartRouter({
        routers: [new RegExpRouter(), new TrieRouter()],
      }),
  })
})
