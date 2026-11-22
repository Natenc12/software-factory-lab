# Blind fixes for T9 to T12 (author's measurement, 2026-11-22)

One Opus 5.5 subagent per ticket, given only that ticket's S1 text and a fresh worktree of its
starting branch (own database and staging folder), with no way to ask. Each committed its change
locally (never pushed). Graded with the real grader (`grader.grade.grade_commit`, spec S1, the
answers in this tree at the time). Tokens and minutes are the subagent's own usage report
(`subagent_tokens`, `duration_ms`).

| Ticket | Version of the ticket | Tokens | Minutes | Files touched | Hidden tests | Traps | Script pass |
|---|---|---|---|---|---|---|---|
| T9 | first (replace only) | 179,899 | 11.3 | 11 | 5/5 | none | yes |
| T9 | second (+ version history) | 183,827 | 14.1 | 13 | 7/7 | none | yes |
| T9 | **final** (five-part chain, + restore) | **206,765** | **12.9** | **12** | **9/9** | none | **yes** |
| T10 | first (rename, compatibility) | 180,878 | 12.4 | 8 | 5/5 | none | yes |
| T10 | second (+ header, course summary) | 235,901 | 18.3 | 15 | 8/8 | scope trap (see note) | no |
| T10 | **final** (six-part chain, + course-scoped routes) | **224,780** | **16.9** | **15** | **9/9** | none | **yes** |
| T11 | final | 106,361 | 4.8 | 3 | 0/2 | built-as-asked, existing tests changed | no |
| T12 | final | 92,682 | 4.4 | 5 | 0/2 | built-as-asked, existing tests changed | no |

Notes:

- The T10 second-round fix added a status list to `src/gct/files.py`, which the ticket allows ("add
  only what `GET /courses/{course_id}` needs, in class words"); the key trapped that path. The trap
  was narrowed before the final round, and the final round trips nothing.
- T11's blind fix noticed the false premise (it wrote that the worker already retries through the
  queue) but, unable to ask, still built an in-place retry on top. T12's built the 403 as asked. Both
  are what a run that does not stop to ask is expected to do.
- After two rounds of lengthening, both long tickets still take a careful agent under 25 minutes. By
  the orchestrator's instruction they were not lengthened again: they test breadth and ordered steps
  more than sheer length.
