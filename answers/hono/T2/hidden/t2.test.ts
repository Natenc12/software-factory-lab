// Hidden tests for T2. The basic, bearer and jwt cases are the upstream fix's own tests
// (honojs/hono#5590); the jwk case is the author's, for the fourth middleware that fix changed.
import { Hono } from '../hono'
import { basicAuth } from '../middleware/basic-auth'
import { bearerAuth } from '../middleware/bearer-auth'
import { jwk } from '../middleware/jwk'
import { jwt } from '../middleware/jwt'

describe('Basic Auth realm', () => {
  it('Should escape double quotes and backslashes in the realm', async () => {
    const app = new Hono()
    app.use('/auth/*', basicAuth({ username: 'user', password: 'pass', realm: 'my "api"\\' }))
    app.get('/auth/*', (c) => c.text('ok'))

    const res = await app.request('http://localhost/auth/page')

    expect(res.status).toBe(401)
    expect(res.headers.get('WWW-Authenticate')).toBe('Basic realm="my \\"api\\"\\\\"')
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
  })
})
