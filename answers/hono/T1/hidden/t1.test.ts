// Hidden tests for T1, from the upstream fix's own tests (honojs/hono#5423).
// A path that repeats a parameter name must yield the first value, whichever router serves it.
import { Hono } from '../hono'
import { TrieRouter } from '../router/trie-router'
import { Node } from '../router/trie-router/node'

describe('TrieRouter node: duplicate param name keeps the first value', () => {
  it('self with trailing static', () => {
    const node = new Node()
    node.insert('get', '/:id/:id/x', 'foo')
    const [res] = node.search('get', '/123/456/x')
    expect(res.length).toBe(1)
    expect(res[0][0]).toBe('foo')
    expect(res[0][1]['id']).toBe('123')
  })

  it('self three times', () => {
    const node = new Node()
    node.insert('get', '/:id/:id/:id', 'foo')
    const [res] = node.search('get', '/1/2/3')
    expect(res.length).toBe(1)
    expect(res[0][0]).toBe('foo')
    expect(res[0][1]['id']).toBe('1')
  })

  it('self with regexp matcher', () => {
    const node = new Node()
    node.insert('get', '/:id/:id{[0-9]+}', 'foo')
    const [res] = node.search('get', '/abc/123')
    expect(res.length).toBe(1)
    expect(res[0][0]).toBe('foo')
    expect(res[0][1]['id']).toBe('abc')
  })
})

describe('TrieRouter: duplicate param name keeps the first value', () => {
  const match = (path: string, url: string) => {
    const router = new TrieRouter<string>()
    router.add('GET', path, 'foo')
    const [res] = router.match('GET', url)
    return res.map(([handler, params]) => ({ handler, params }))
  }

  it('self with trailing static', () => {
    const res = match('/:id/:id/x', '/123/456/x')
    expect(res.length).toBe(1)
    expect(res[0].handler).toEqual('foo')
    expect(res[0].params['id']).toBe('123')
  })

  it('self three times', () => {
    const res = match('/:id/:id/:id', '/1/2/3')
    expect(res.length).toBe(1)
    expect(res[0].handler).toEqual('foo')
    expect(res[0].params['id']).toBe('1')
  })
})

describe('Hono: duplicate param name is stable across SmartRouter fallback', () => {
  it('returns the first id whether or not an unrelated route is registered', async () => {
    const a = new Hono()
    a.get('/:id/:id/x', (c) => c.text(c.req.param('id')))
    const resA = await a.request('/123/456/x')
    expect(resA.status).toBe(200)
    expect(await resA.text()).toBe('123')

    const b = new Hono()
    b.get('/:id/:id/x', (c) => c.text(c.req.param('id')))
    b.get('/a', (c) => c.text('a'))
    const resB = await b.request('/123/456/x')
    expect(resB.status).toBe(200)
    expect(await resB.text()).toBe('123')
    expect(b.router.name).toBe('SmartRouter + TrieRouter')
  })
})
