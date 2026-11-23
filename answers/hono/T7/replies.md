# T7 replies (stand-in owner)

## T7-open-decision
When: The developer asks what `*` in an origin pattern may match (one label or several, which characters), whether the bare domain or another scheme or port matches, or proposes a matching rule and asks for confirmation, or lists options for it.
Reply: `*` stands for one or more DNS labels, each made of letters, digits or hyphens, so a subdomain at any depth: `https://*.example.com` matches `https://app.example.com` and `https://acme.eu.example.com`, but not the bare `https://example.com`. The scheme must match exactly, and so must the port: a pattern without a port matches only origins without one, and `https://*.example.com:8443` matches only port 8443.

## T7-other-positions
When: The developer asks, and has not planned or made the change, whether `*` should also work elsewhere in the host (such as `https://app.*.com`) or in the scheme or port.
Reply: No. Only a `*.` at the very start of the host is a pattern; any other string is compared exactly, as today.

## T7-function-origin
When: The developer asks, and has not planned or made the change, whether a function given as `origin` should also receive or apply patterns.
Reply: No, a function keeps full control and is unchanged.
