---
name: prove-each-claim
description: Use before writing a pull request description or any report line that says something passes, fails, works, was tested or was checked.
---
List every claim you are about to make. Next to each, put the command you ran in this session and
what it printed. A claim about the old code ("these tests fail without my change") needs a run on the
starting commit, not a guess. Take numbers from tool output, not memory.

Drop or soften any claim you cannot back: "not checked" is better than a wrong "checked". Then write
the description: what was wrong, what you changed, how you tested it (the commands), and what you
did not check.
