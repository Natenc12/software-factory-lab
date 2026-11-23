# T3 replies (stand-in owner)

## T3-bun-error-hook
When: The developer asks whether adding Bun's own `error` hook to the exported handler object is enough, or whether `open`, `message` and `close` should catch errors themselves.
Reply: `open`, `message` and `close` must deliver the error to `onError` themselves, so a direct call reaches it. You may add Bun's hook as well, but it is not enough on its own.

## T3-no-onerror
When: The developer asks what should happen to an error when the app set no `onError`.
Reply: Let it propagate exactly as today. Nothing may be swallowed silently.

## T3-adapters-copy
When: The developer asks whether to change the copy in `adapters/bun` (the `@hono/bun` package) too.
Reply: Yes, keep the two in step.
