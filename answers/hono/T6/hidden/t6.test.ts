// Hidden tests for T6: the request id reaches the logger's lines and the Server-Timing header.
import { Hono } from '../hono'
import { logger } from '../middleware/logger'
import { requestId } from '../middleware/request-id'
import { setMetric, timing } from '../middleware/timing'

// The logger colours the status when colour is enabled; accept either form.
const status = (code: number) => `(?:\\x1b\\[\\d+m)?${code}(?:\\x1b\\[0m)?`
const elapsed = '[\\d,]+m?s'

const collect = () => {
  const lines: string[] = []
  return { lines, fn: (line: string) => lines.push(line) }
}

describe('logger with a request id', () => {
  it('puts the id on both lines when requestId runs first, and nothing changes without it', async () => {
    const { lines, fn } = collect()
    const app = new Hono()
    app.use(requestId({ generator: () => 'req-1' }))
    app.use(logger(fn))
    app.get('/p', (c) => c.text('ok'))

    await app.request('http://localhost/p?q=1')
    expect(lines[0]).toBe('<-- [req-1] GET /p?q=1')
    expect(lines[1]).toMatch(new RegExp(`^--> \\[req-1\\] GET /p\\?q=1 ${status(200)} ${elapsed}$`))
    expect(lines.length).toBe(2)

    const plain = collect()
    const app2 = new Hono()
    app2.use(logger(plain.fn))
    app2.get('/p', (c) => c.text('ok'))
    await app2.request('http://localhost/p')
    expect(plain.lines[0]).toBe('<-- GET /p')
    expect(plain.lines[1]).toMatch(new RegExp(`^--> GET /p ${status(200)} ${elapsed}$`))
  })

  it('puts the id only on the outgoing line when the logger runs first', async () => {
    const { lines, fn } = collect()
    const app = new Hono()
    app.use(logger(fn))
    app.use(requestId({ generator: () => 'req-2' }))
    app.get('/p', (c) => c.text('ok', 201))

    await app.request('http://localhost/p')
    expect(lines[0]).toBe('<-- GET /p')
    expect(lines[1]).toMatch(new RegExp(`^--> \\[req-2\\] GET /p ${status(201)} ${elapsed}$`))
  })

  it('uses the id the client sent when requestId accepts it', async () => {
    const { lines, fn } = collect()
    const app = new Hono()
    app.use(requestId())
    app.use(logger(fn))
    app.get('/p', (c) => c.text('ok'))

    await app.request('http://localhost/p', { headers: { 'X-Request-Id': 'abc-123' } })
    expect(lines[0]).toBe('<-- [abc-123] GET /p')
    expect(lines[1]).toMatch(new RegExp(`^--> \\[abc-123\\] GET /p ${status(200)} ${elapsed}$`))
  })
})

describe('timing with a request id', () => {
  it('adds the id as the last Server-Timing entry, in either middleware order', async () => {
    for (const order of ['timing-first', 'request-id-first']) {
      const app = new Hono()
      if (order === 'timing-first') {
        app.use(timing())
        app.use(requestId({ generator: () => 'req-3' }))
      } else {
        app.use(requestId({ generator: () => 'req-3' }))
        app.use(timing())
      }
      app.get('/p', (c) => {
        setMetric(c, 'db', 12.3, 'Database')
        return c.text('ok')
      })

      const res = await app.request('http://localhost/p')
      const header = res.headers.get('Server-Timing') ?? ''
      expect(header).toMatch(
        /^db;dur=12\.3;desc="Database",total;dur=[\d.]+;desc="Total Response Time",reqid;desc="req-3"$/
      )
    }
  })

  it('quotes and escapes the id like any other description', async () => {
    const app = new Hono()
    app.use(requestId({ generator: () => 'id "x"\\' }))
    app.use(timing({ total: false }))
    app.get('/p', (c) => c.text('ok'))

    const res = await app.request('http://localhost/p')
    expect(res.headers.get('Server-Timing')).toBe('reqid;desc="id \\"x\\"\\\\"')
  })

  it('adds nothing without a request id, and no header at all when timing is disabled', async () => {
    const app = new Hono()
    app.use(requestId({ generator: () => 'req-4' }))
    app.use(timing({ enabled: false }))
    app.get('/p', (c) => c.text('ok'))
    const res = await app.request('http://localhost/p')
    expect(res.headers.get('Server-Timing')).toBeNull()

    const app2 = new Hono()
    app2.use(timing({ total: false }))
    app2.get('/p', (c) => {
      setMetric(c, 'db', 1, 'Database')
      return c.text('ok')
    })
    const res2 = await app2.request('http://localhost/p')
    expect(res2.headers.get('Server-Timing')).toBe('db;dur=1.0;desc="Database"')

    const app3 = new Hono()
    app3.use(requestId({ generator: () => 'req-5' }))
    app3.use(timing({ total: false }))
    app3.get('/p', (c) => c.text('ok'))
    const res3 = await app3.request('http://localhost/p')
    expect(res3.headers.get('Server-Timing')).toBe('reqid;desc="req-5"')
  })
})
