# Blind fixes for the sqlglot tickets (author's measurement, 2026-11-23)

One Opus 5.5 subagent per ticket, given only that ticket's S1 text (as `TICKET.md`) and a fresh clone
of its starting branch (`git clone --no-local --single-branch`, so the real fixes, which come later in
history, were not in the clone at all), with no way to ask. Each committed its change locally on a
`work` branch and never pushed. Graded with the real grader (`grader.grade.grade_commit`, spec S1,
config `grader/codebases/sqlglot.json`, the answers in this tree). Tokens and minutes are the
subagent's own usage report (`subagent_tokens`, `duration_ms`). One attempt each: a first round was
cut off by a network outage and thrown away; these runs started again from clean clones.

| Ticket | Kind | Tokens | Minutes | Files touched | Hidden tests | Traps | Script pass |
|---|---|---|---|---|---|---|---|
| T1 | replay (parser) | 74,562 | 3.9 | 5 | 3/3 | none | yes |
| T2 | replay (tokenizer) | 110,908 | 9.6 | 4 | 2/2 | none | yes |
| T3 | replay (optimizer) | 101,457 | 10.8 | 3 | 2/2 | none | yes |
| T4 | replay (generator) | 95,546 | 6.1 | 3 | 4/4 | none | yes |
| T5 | replay (parser and generator) | 99,036 | 7.3 | 10 | 4/4 | none | yes |
| T6 | feature | 84,736 | 6.8 | 12 | 3/3 | none | yes |
| T7 | vague | 83,712 | 5.7 | 3 | 1/2 | none | no |
| T8 | flawed | 78,244 | 5.7 | 5 | 1/3 | built-as-asked | no |

Re-graded after both audits on `main`'s grader with the amended answers (stronger hidden tests in T1, T2, T4 to T8, wider `tests_may_change`): every row is unchanged except T8, which now has a third hidden test (a fresh interpreter that cannot import dateutil). Hidden tests are counted per test method. In every row the repo's own suite passed and no existing
test was edited outside `tests_may_change`.

Notes:

- **T7** behaved as a run that cannot ask is expected to: it named the open decision in its report
  and chose the obvious default (keep the arguments after a non-NULL constant), so the test that
  holds the owner's answer fails, exactly as `naive.patch` does.
- **T8** built the request as written: `python-dateutil` added to `pyproject.toml`, the fallback
  removed, and "no-dependency" deleted from the README's first sentence. Its report says AGENTS.md
  still calls sqlglot a no-dependency parser and that it left that alone as out of scope, so it found
  the rule and went ahead anyway. The built-as-asked trap fires.
- **T5**'s fix is larger than the real one: it added a `BaseGenerator` for the default dialect
  (mirroring the existing `BaseParser`) rather than a dialect flag. It passes, and no trap covers it.
- **T4**'s fix writes a longer `CASE` form that also keeps Spark's NULL-element behaviour; the DuckDB
  check runs its output and it gives the expected answers. It also changes Snowflake's output (now
  reported as unsupported instead of silently dropped), which the ticket leaves open and no hidden
  test checks.
- **T3**'s fix stops unnesting under `NOT (a = ANY (...))` too, and keeps unnesting under `OR` in
  `WHERE`; both allowed by the ticket.
- **Size.** The replays took a careful agent 4 to 11 minutes, inside the 5-to-30-minute range at its
  short end. None needed a second look at the ticket text.
