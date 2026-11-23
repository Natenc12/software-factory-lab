---
name: check-the-ask
description: Use right after reading the ticket and the code it touches, before planning or changing anything, and whenever the ticket seems to clash with the code, its tests, its docs or a recorded decision.
---
Write down, one line each, what the ticket asks for. Search for rules that touch it: decision
records, docs, comments, tests that pin current behaviour, config limits. For each rule the ticket
would break, note the file and line.

If one breaks, do not build either version yet. Write the owner a short page in your scratch folder:
what the ticket asks, what it conflicts with (with the example), and the reading you recommend. Then
stop and ask.

If nothing breaks, say in one line that you checked, and where.
