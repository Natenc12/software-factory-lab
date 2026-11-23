# T2 replies (stand-in owner)

## T2-which-middlewares
When: The developer asks which middlewares the fix should cover, or whether `jwt` and `jwk` are included.
Reply: All four that write a realm into `WWW-Authenticate`: basicAuth, bearerAuth, jwt and jwk, including the `error_description` value in jwt and jwk.

## T2-escape-rule
When: The developer asks how a backslash or a double quote in the realm should appear in the header, or whether to strip or reject such characters instead of escaping them.
Reply: Escape them: a backslash becomes `\\` and a double quote becomes `\"`, and every other character stays as it is. Do not strip or reject anything.
