---
name: test-that-bites
description: Use when adding or changing tests for a change.
---
Test what a user of the code can see, not its insides. Run each new test on the starting commit and
confirm it fails for the reason you expect, then confirm it passes on your change. Keep a list of
the tests you checked that way.

Do not edit or delete existing tests unless the ticket asks. If an old test blocks you, that is a
question for the owner.
