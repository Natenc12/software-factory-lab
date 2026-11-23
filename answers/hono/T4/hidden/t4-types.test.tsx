// Hidden test for T4 (audit B): the component type accepts an async component that returns null, as
// it accepts a sync one. vitest strips types, so this spawns tsc on a few lines against the built
// declarations, the way the repository's own build/jsx-types.test.ts does.
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
  }, 60_000)
})
