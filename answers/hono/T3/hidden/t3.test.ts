// Hidden tests for T3, from the upstream fix's own tests (honojs/hono#5620). One change: the async
// case waits for a macrotask (setTimeout 0) instead of exactly one microtask, so a correct fix that
// takes a few more promise steps to deliver the rejection still passes. The upstream test that an
// error is rethrown without onError passes on the base, so it is folded into the end of the first test.
import type { BunServerWebSocket, BunWebSocketData } from '../adapter/bun/websocket'
import { websocket } from '../adapter/bun/websocket'

describe('Bun websocket handler: onError', () => {
  const createSocket = (events: BunWebSocketData['events']) =>
    ({
      data: { events, url: new URL('http://localhost'), protocol: '' },
      readyState: 1,
    }) as BunServerWebSocket<BunWebSocketData>

  it('Should pass an error thrown by a handler to onError', () => {
    const onError = vi.fn()
    const error = new Error('boom')
    const ws = createSocket({
      onOpen: () => {
        throw error
      },
      onMessage: () => {
        throw error
      },
      onClose: () => {
        throw error
      },
      onError,
    })

    websocket.open(ws)
    websocket.message(ws, 'message')
    websocket.close(ws)

    expect(onError).toHaveBeenCalledTimes(3)
    const [evt, context] = onError.mock.calls[0]
    expect(evt.type).toBe('error')
    expect(evt.error).toBe(error)
    expect(context.raw).toBe(ws)

    // Without onError, the error still propagates as before.
    const bare = createSocket({
      onMessage: () => {
        throw error
      },
    })
    expect(() => websocket.message(bare, 'message')).toThrow(error)
  })

  it('Should pass a rejection of an async handler to onError', async () => {
    const onError = vi.fn()
    const error = new Error('boom')
    const ws = createSocket({
      onMessage: async () => {
        throw error
      },
      onError,
    })

    websocket.message(ws, 'message')
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(onError).toHaveBeenCalledTimes(1)
    expect(onError.mock.calls[0][0].error).toBe(error)
  })
})
