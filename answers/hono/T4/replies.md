# T4 replies (stand-in owner)

## T4-true-and-zero
When: The developer asks how `true`, `0` or another number returned by an async component should render.
Reply: Exactly as the same value returned by a sync component: `true` renders as nothing, and a number renders as its digits, so `0` renders as `0`.

## T4-dom-renderer
When: The developer asks whether to change the client-side renderer in `src/jsx/dom/` as well.
Reply: No, leave `src/jsx/dom/` as it is; this ticket is about rendering on the server and the `html` tag.
