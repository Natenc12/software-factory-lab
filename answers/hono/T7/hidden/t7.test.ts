// Hidden tests for T7: wildcard origins in cors() and csrf(), with the owner's answer to the open
// decision: `*` matches one or more DNS labels (each letters, digits, hyphens), so a subdomain at any
// depth; the bare domain does not match, and scheme and port must match exactly.
import { Hono } from '../hono'
import { cors } from '../middleware/cors'
import { csrf } from '../middleware/csrf'

const corsApp = (origin: string | string[]) => {
  const app = new Hono()
  app.use('*', cors({ origin }))
  app.get('/api', (c) => c.text('ok'))
  return app
}

const allowOrigin = async (app: Hono, origin: string) => {
  const res = await app.request('http://localhost/api', { headers: { Origin: origin } })
  return res.headers.get('Access-Control-Allow-Origin')
}

const csrfApp = (origin: string | string[]) => {
  const app = new Hono()
  app.use('*', csrf({ origin }))
  app.post('/form', (c) => c.text('ok'))
  return app
}

const post = async (app: Hono, origin: string) => {
  const res = await app.request('http://localhost/form', {
    method: 'POST',
    headers: { Origin: origin, 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'a=1',
  })
  return res.status
}

describe('cors() with a wildcard origin', () => {
  it('allows a subdomain at any depth and refuses everything else', async () => {
    const app = corsApp('https://*.example.com')
    expect(await allowOrigin(app, 'https://app.example.com')).toBe('https://app.example.com')
    expect(await allowOrigin(app, 'https://my-app2.example.com')).toBe(
      'https://my-app2.example.com'
    )
    expect(await allowOrigin(app, 'https://acme.eu.example.com')).toBe(
      'https://acme.eu.example.com'
    )

    for (const refused of [
      'https://app.examplexcom',
      'https://app.example-com',
      'https://example.com',
      'https://.example.com',
      'https://a..example.com',
      'http://app.example.com',
      'https://app.example.com:8443',
      'https://appexample.com',
      'https://evil-example.com',
      'https://app.example.com.evil.net',
      'https://app_1.example.com',
    ]) {
      expect(await allowOrigin(app, refused), refused).toBeNull()
    }

    // a `*` anywhere else is not a pattern: compared exactly, as today (audit A)
    expect(await allowOrigin(corsApp('https://app.*.com'), 'https://app.example.com')).toBeNull()
    expect(await allowOrigin(corsApp('https://example.*'), 'https://example.com')).toBeNull()
    expect(await allowOrigin(corsApp(['https://app.*.com']), 'https://app.example.com')).toBeNull()
  })

  it('matches the port given in the pattern, and mixes with exact origins in a list', async () => {
    const app = corsApp(['https://*.example.com:8443', 'https://partner.org'])
    expect(await allowOrigin(app, 'https://app.example.com:8443')).toBe(
      'https://app.example.com:8443'
    )
    expect(await allowOrigin(app, 'https://partner.org')).toBe('https://partner.org')
    expect(await allowOrigin(app, 'https://app.example.com')).toBeNull()
    expect(await allowOrigin(app, 'https://app.partner.org')).toBeNull()

    const res = await app.request('http://localhost/api', {
      headers: { Origin: 'https://app.example.com:8443' },
    })
    expect(res.headers.get('Vary')).toBe('Origin')
  })

  it('works for any domain, scheme and port, not only the examples', async () => {
    const app = corsApp('http://*.internal.test:3000')
    expect(await allowOrigin(app, 'http://api.internal.test:3000')).toBe(
      'http://api.internal.test:3000'
    )
    expect(await allowOrigin(app, 'http://x.y.internal.test:3000')).toBe(
      'http://x.y.internal.test:3000'
    )
    expect(await allowOrigin(app, 'http://api.internal.test')).toBeNull()
    expect(await allowOrigin(app, 'https://api.internal.test:3000')).toBeNull()
    expect(await allowOrigin(app, 'http://api.example.com:3000')).toBeNull()
  })

  it('answers a preflight for a matching origin', async () => {
    const app = corsApp('https://*.example.com')
    const res = await app.request('http://localhost/api', {
      method: 'OPTIONS',
      headers: { Origin: 'https://app.example.com', 'Access-Control-Request-Method': 'PUT' },
    })
    expect(res.status).toBe(204)
    expect(res.headers.get('Access-Control-Allow-Origin')).toBe('https://app.example.com')
  })
})

describe('csrf() with a wildcard origin', () => {
  it('accepts a subdomain at any depth and refuses everything else', async () => {
    const app = csrfApp('https://*.example.com')
    expect(await post(app, 'https://app.example.com')).toBe(200)
    expect(await post(app, 'https://acme.eu.example.com')).toBe(200)

    for (const refused of [
      'https://app.examplexcom',
      'https://example.com',
      'http://app.example.com',
      'https://app.example.com:8443',
      'https://app.example.com.evil.net',
    ]) {
      expect(await post(app, refused), refused).toBe(403)
    }

    // a `*` anywhere else is not a pattern (audit A)
    expect(await post(csrfApp('https://app.*.com'), 'https://app.example.com')).toBe(403)
  })

  it('mixes with exact origins in a list', async () => {
    const app = csrfApp(['https://partner.org', 'https://*.example.com'])
    expect(await post(app, 'https://partner.org')).toBe(200)
    expect(await post(app, 'https://admin.example.com')).toBe(200)
    expect(await post(app, 'https://x.partner.org')).toBe(403)
  })
})
