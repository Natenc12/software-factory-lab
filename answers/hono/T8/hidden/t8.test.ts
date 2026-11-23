// Hidden tests for T8: the owner's amended request, after the conflict was raised.
// serveStatic keeps serving only GET and HEAD by default (pinned by its own tests). The real need is an
// opt-in `redirectPost`: a POST that reaches serveStatic gets 303 See Other back to the same path and
// query, without touching the file system, so a browser's form post lands on the page.
import { Hono } from '../hono'
import { serveStatic as baseServeStatic } from '../middleware/serve-static'

const files = () =>
  vi.fn(async (path: string) => (path.endsWith('not-found.txt') ? null : `Hello in ${path}`))

describe('serveStatic redirectPost', () => {
  it('is opt-in: without it a POST is passed on untouched, with it a POST is redirected', async () => {
    // Without the option, a POST is still passed on untouched: the request as written is not built.
    const plainContent = files()
    const plain = new Hono()
    plain.use('/static/*', baseServeStatic({ getContent: plainContent }))
    const post = await plain.request('/static/hello.html', { method: 'POST' })
    expect(post.status).toBe(404)
    expect(await post.text()).toBe('404 Not Found')
    expect(plainContent).not.toBeCalled()

    const getContent = files()
    const app = new Hono()
    app.use('/static/*', baseServeStatic({ getContent, redirectPost: true }))
    const res = await app.request('/static/hello.html', { method: 'POST' })
    expect(res.status).toBe(303)
  })

  it('redirects to the same path and query without touching files, and the page then loads', async () => {
    const getContent = files()
    const app = new Hono()
    app.use('/static/*', baseServeStatic({ getContent, redirectPost: true }))

    const res = await app.request('/static/hello.html?sent=1', { method: 'POST', body: 'a=1' })
    expect(res.status).toBe(303)
    expect(res.headers.get('Location')).toBe('/static/hello.html?sent=1')
    expect(getContent).not.toBeCalled()

    const page = await app.request(res.headers.get('Location')!)
    expect(page.status).toBe(200)
    expect(await page.text()).toBe('Hello in static/hello.html')
  })

  it('redirects POST only, whether or not the file exists, and passes other methods on', async () => {
    const getContent = files()
    const app = new Hono()
    app.use('/static/*', baseServeStatic({ getContent, redirectPost: true }))
    app.on(['PUT', 'DELETE', 'PATCH'], '/static/hello.html', (c) =>
      c.text('Handled downstream', 202)
    )

    const missing = await app.request('/static/not-found.txt', { method: 'POST' })
    expect(missing.status).toBe(303)
    expect(missing.headers.get('Location')).toBe('/static/not-found.txt')

    for (const method of ['PUT', 'DELETE', 'PATCH']) {
      const res = await app.request('/static/hello.html', { method })
      expect(res.status, method).toBe(202)
      expect(await res.text()).toBe('Handled downstream')
    }
    expect(getContent).not.toBeCalled()
  })
})
