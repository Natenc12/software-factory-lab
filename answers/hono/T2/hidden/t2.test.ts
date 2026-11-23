// Hidden tests for T2. The basic, bearer and jwt cases are the upstream fix's own tests
// (honojs/hono#5590); the jwk case is the author's, for the fourth middleware that fix changed.
import { Hono } from '../hono'
import { basicAuth } from '../middleware/basic-auth'
import { bearerAuth } from '../middleware/bearer-auth'
import { jwk } from '../middleware/jwk'
import { jwt } from '../middleware/jwt'

// A realm with a backslash in the middle, quotes and a trailing backslash (audit A), so a rule that fits
// only each middleware's own example fails.
const MIXED = 'a\\b "c"\\'
const MIXED_ESCAPED = 'a\\\\b \\"c\\"\\\\'
const NO_AUTH = ',error="invalid_request",error_description="no authorization included in request"'

describe('Basic Auth realm', () => {
  it('Should escape double quotes and backslashes in the realm', async () => {
    const app = new Hono()
    app.use('/auth/*', basicAuth({ username: 'user', password: 'pass', realm: 'my "api"\\' }))
    app.get('/auth/*', (c) => c.text('ok'))

    const res = await app.request('http://localhost/auth/page')

    expect(res.status).toBe(401)
    expect(res.headers.get('WWW-Authenticate')).toBe('Basic realm="my \\"api\\"\\\\"')

    const mixed = new Hono()
    mixed.use('/auth/*', basicAuth({ username: 'user', password: 'pass', realm: MIXED }))
    mixed.get('/auth/*', (c) => c.text('ok'))
    const res2 = await mixed.request('http://localhost/auth/page')
    expect(res2.headers.get('WWW-Authenticate')).toBe(`Basic realm="${MIXED_ESCAPED}"`)
  })
})

describe('Bearer Auth realm', () => {
  it('Should escape double quotes and backslashes in the realm', async () => {
    const app = new Hono()
    app.use('/auth/*', bearerAuth({ token: 'secret', realm: 'my "api"\\' }))
    app.get('/auth/*', (c) => c.text('ok'))

    const res = await app.request('http://localhost/auth/page')

    expect(res.status).toBe(401)
    expect(res.headers.get('WWW-Authenticate')).toBe('Bearer realm="my \\"api\\"\\\\"')

    const mixed = new Hono()
    mixed.use('/auth/*', bearerAuth({ token: 'secret', realm: MIXED }))
    mixed.get('/auth/*', (c) => c.text('ok'))
    const res2 = await mixed.request('http://localhost/auth/page')
    expect(res2.headers.get('WWW-Authenticate')).toBe(`Bearer realm="${MIXED_ESCAPED}"`)
  })
})

describe('JWT realm', () => {
  it('Should escape backslashes in the realm', async () => {
    const app = new Hono()
    app.use('/auth/*', jwt({ secret: 'a-secret', alg: 'HS256', realm: 'my\\api\\' }))
    app.get('/auth/*', (c) => c.text('ok'))

    const res = await app.request('http://localhost/auth/page')

    expect(res.status).toBe(401)
    expect(res.headers.get('WWW-Authenticate')).toBe(
      'Bearer realm="my\\\\api\\\\",error="invalid_request",error_description="no authorization included in request"'
    )

    const mixed = new Hono()
    mixed.use('/auth/*', jwt({ secret: 'a-secret', alg: 'HS256', realm: MIXED }))
    mixed.get('/auth/*', (c) => c.text('ok'))
    const res2 = await mixed.request('http://localhost/auth/page')
    expect(res2.headers.get('WWW-Authenticate')).toBe(`Bearer realm="${MIXED_ESCAPED}"${NO_AUTH}`)
  })
})

describe('JWK realm', () => {
  it('Should escape backslashes in the realm', async () => {
    const app = new Hono()
    app.use('/auth/*', jwk({ keys: [], alg: ['RS256'], realm: 'my\\api\\' }))
    app.get('/auth/*', (c) => c.text('ok'))

    const res = await app.request('http://localhost/auth/page')

    expect(res.status).toBe(401)
    expect(res.headers.get('WWW-Authenticate')).toBe(
      'Bearer realm="my\\\\api\\\\",error="invalid_request",error_description="no authorization included in request"'
    )

    const mixed = new Hono()
    mixed.use('/auth/*', jwk({ keys: [], alg: ['RS256'], realm: MIXED }))
    mixed.get('/auth/*', (c) => c.text('ok'))
    const res2 = await mixed.request('http://localhost/auth/page')
    expect(res2.headers.get('WWW-Authenticate')).toBe(`Bearer realm="${MIXED_ESCAPED}"${NO_AUTH}`)
  })
})
