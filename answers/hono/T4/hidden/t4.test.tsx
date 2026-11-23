// Hidden tests for T4, from the upstream fix's own tests (honojs/hono#5594). Changes: the rows that
// already pass on the base (a sync component, an async component returning a string) are left out,
// and the streaming test reads the Suspense id from the first chunk instead of counting renders.
import { JSDOM } from 'jsdom'
import { html } from '../helper/html'
import { Suspense, renderToReadableStream } from '../jsx/streaming'

function replacementResult(source: string) {
  const document = new JSDOM(source, { runScripts: 'dangerously' }).window.document
  document.querySelectorAll('template, script').forEach((e) => e.remove())
  return document.body.innerHTML
}

describe('html`` with a promise of a non-string value', () => {
  it.each([
    [null, '<p></p>'],
    [undefined, '<p></p>'],
    [false, '<p></p>'],
    [true, '<p></p>'],
    [0, '<p>0</p>'],
    [1, '<p>1</p>'],
  ])('Should render Promise<%s> like the same sync value', async (value, expected) => {
    const res = html`<p>${Promise.resolve(value)}</p>`
    expect(res).toBeInstanceOf(Promise)
    expect((await res).toString()).toBe(expected)
  })
})

describe('async component returning a non-element value', () => {
  it.each([
    [null, '<div></div>'],
    [undefined, '<div></div>'],
    [false, '<div></div>'],
    [true, '<div></div>'],
    [0, '<div>0</div>'],
    [1, '<div>1</div>'],
  ])('Component returning %s renders like the sync one', async (value, expected) => {
    const SyncValue = () => value
    const AsyncValue = async () => value
    expect(
      (
        <div>
          <SyncValue />
        </div>
      ).toString()
    ).toBe(expected)
    expect(
      (
        await (
          <div>
            <AsyncValue />
          </div>
        ).toString()
      ).toString()
    ).toBe(expected)
  })
})

describe('streaming: async component returning a non-element value', () => {
  it.each([
    [null, ''],
    [false, ''],
    [1, '1'],
  ])('async component returning %s', async (value, expected) => {
    const Content = async () => value

    const stream = renderToReadableStream(
      <Suspense fallback={<p>Loading...</p>}>
        <Content />
      </Suspense>
    )

    const chunks: string[] = []
    const textDecoder = new TextDecoder()
    for await (const chunk of stream as any) {
      chunks.push(textDecoder.decode(chunk))
    }

    const id = /<template id="(H:\d+)"><\/template>/.exec(chunks[0] ?? '')?.[1]
    expect(id).toBeDefined()
    expect(chunks[0]).toBe(`<template id="${id}"></template><p>Loading...</p><!--/$-->`)
    expect(chunks.length).toBe(2)
    expect(
      chunks[1].startsWith(`<template data-hono-target="${id}">${expected}</template><script>`)
    ).toBe(true)
    expect(replacementResult(`<html><body>${chunks.join('')}</body></html>`)).toEqual(expected)
  })
})
