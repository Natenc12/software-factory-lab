# Bearer auth: tidy the missing-options error

When `bearerAuth` is called with neither `token` nor `verifyToken`, the error message it throws starts with a lower-case word. Make that message start with a capital letter, and make sure a test covers the exact message.
