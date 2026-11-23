// Hidden tests for T5. The first is the upstream fix's own client test (honojs/hono#5650), with two
// checks folded in that already hold on the base (plain init keys from both levels still arrive). The
// second is the author's: the same rule for another class instance, a Node `dispatcher`. The upstream
// unit tests of the internal `deepMerge` helper are left out, so a fix elsewhere in the client passes.
import { hc } from '../client'

describe('hc: init options set on the client and on the request', () => {
  it('keeps a valid AbortSignal when both the client and the request set one', async () => {
    const requestController = new AbortController()
    let received: RequestInit | undefined
    const client = hc<any>('http://localhost', {
      init: { signal: new AbortController().signal, credentials: 'include' },
      fetch: async (input: RequestInfo | URL, init?: RequestInit) => {
        received = init
        new Request(input, init)
        return new Response('ok')
      },
    })

    await client.headers.$get(undefined, {
      init: { signal: requestController.signal, mode: 'cors' },
    })

    expect(received?.signal).toBe(requestController.signal)
    expect(received?.signal).toBeInstanceOf(AbortSignal)
    expect(received?.credentials).toBe('include')
    expect(received?.mode).toBe('cors')
  })

  it('passes any class instance in init through as it is, the request one winning', async () => {
    class Dispatcher {
      constructor(public name: string) {}
    }
    const clientDispatcher = new Dispatcher('client')
    const requestDispatcher = new Dispatcher('request')
    let received: (RequestInit & { dispatcher?: unknown }) | undefined
    const client = hc<any>('http://localhost', {
      init: { dispatcher: clientDispatcher } as RequestInit,
      fetch: async (_input: RequestInfo | URL, init?: RequestInit) => {
        received = init
        return new Response('ok')
      },
    })

    await client.items.$get(undefined, { init: { dispatcher: requestDispatcher } as RequestInit })
    expect(received?.dispatcher).toBe(requestDispatcher)

    await client.items.$get(undefined, { init: { cache: 'no-store' } })
    expect(received?.dispatcher).toBe(clientDispatcher)
  })
})
