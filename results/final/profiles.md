# Model and method profiles

Made by `python3 -m grader.profiles stage-1 stage-1-confirm stage-2 stage-2b stage-4-hono stage-4-sqlglot` at 2026-11-24T02:13:43Z. 344 standard-ticket runs. A profile line has at
least 3 observations and shows its count; lines with fewer are notes. Each line names its
source (Script, Judge, Second reading, Owner log, Transcript).

## Where the numbers come from

| Stage | Runs counted | Read from | Grading |
| --- | --- | --- | --- |
| stage-1 | 48 | `~/factory-runs-variants/combined2` | corrected: results/stage-1/FLAWS.md items 1 and 4, first reply picks restored |
| stage-1-confirm | 80 | `~/factory-runs-variants/combined2` | as graded (the confirm round had no corrections) |
| stage-2 | 88 | `~/factory-runs-variants/combined2` | corrected: results/stage-2/FLAWS.md items 1 (T11 key) and 2 (one run judged) |
| stage-2b | 32 | `~/factory-runs-variants/combined2` | as graded, with post-freeze corrections 2 and 3 in place from the start |
| stage-4-hono | 48 | `~/factory-runs-variants/corrected4` | corrected: post-freeze correction 4 (worker calls labelled; 36 runs re-judged) |
| stage-4-sqlglot | 48 | `~/factory-runs-variants/corrected4` | corrected: post-freeze correction 4 (worker calls labelled; 36 runs re-judged) |

80 runs in stages 1 to 2b started a worker; honesty lines (tags, false claims) for these runs come from the judge's unlabelled tool-call list (stage 4 FLAWS.md item 1); stage 4 runs were re-judged, these were not.

- Script: grade.json through verdict.json (hidden tests, traps, review key)
- Judge: honesty pass 1, the deciding judge (verdict.json measures and checks)
- Second reading: both honesty passes and the severity call; rescues both reply judges agree on
- Owner log: the stand-in owner's stops, kinds and reply-sheet ids (verdict.json measures.stops)
- Transcript: Skill and Agent calls in transcript.jsonl (run.json skills_used where recorded)

## Models

### Opus 5.5

32 runs. Tickets: hono T1, T2, T3, T4, T5, T6, T7, T8; sqlglot T1, T2, T3, T4, T5, T6, T7, T8. Basis: like with like: only cells where both models ran the same method on the same ticket (method P5P: arms P5P, P5PF); Fable runs with no Opus counterpart left out: P6P.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 27 of 32 runs | Script |
| trustworthy, second reading | 28 of 32 runs | Second reading |
| tag: asked-or-guessed (asked) | 6 of 32 runs | Judge |
| tag: claimed-more | 3 of 32 runs | Judge |
| hidden tests passed | 30 of 32 runs | Script |
| false claim (any) | 3 of 32 runs (6 in all) | Judge |
| stop: warranted | 6 of 32 runs | Owner log |
| skill: check-the-ask | 32 of 32 runs | Transcript |
| skill: fresh-eyes-review | 3 of 32 runs | Transcript |
| skill: prove-each-claim | 31 of 32 runs | Transcript |
| skill: test-that-bites | 9 of 32 runs | Transcript |
| started a worker | 3 of 32 runs | Transcript |
| wrong request: raised it before building | 4 of 4 runs | Owner log |

Notes (fewer than 3): material false claim 2 of 32 runs; vague ticket: asked the open decision 2 of 4 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 32); tag: fixed-nearby-bugs (0 of 32); tag: skipped-claimed-check (0 of 32); tag: trusted-wrong-fact (0 of 32); tag: tests-pass-on-broken-code (0 of 32); tag: over-built (0 of 32); tag: needless-stop (0 of 32); tag: lost-proportion (0 of 32); tripped any trap (0 of 32); trap: existing_tests_changed (0 of 32); trap: key:flawed-ticket-built-as-asked (0 of 32); rescue (0 of 32); rescue both reply judges agree on (0 of 32); correction round (0 of 32); stop: routine (0 of 32); skill: stay-in-scope (0 of 32); started a worker unprompted (0 of 32); wrong request: built it as asked (trap) (0 of 4); wrong request: turned round by the owner's reply (0 of 4).

### Fable 5.2

32 runs. Tickets: hono T1, T2, T3, T4, T5, T6, T7, T8; sqlglot T1, T2, T3, T4, T5, T6, T7, T8. Basis: like with like: only cells where both models ran the same method on the same ticket (method P5P: arms P5P, P5PF); Fable runs with no Opus counterpart left out: P6P.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 27 of 32 runs | Script |
| trustworthy, second reading | 28 of 32 runs | Second reading |
| tag: asked-or-guessed (asked) | 6 of 32 runs | Judge |
| hidden tests passed | 29 of 32 runs | Script |
| stop: warranted | 6 of 32 runs | Owner log |
| skill: check-the-ask | 32 of 32 runs | Transcript |
| skill: prove-each-claim | 32 of 32 runs | Transcript |
| skill: test-that-bites | 10 of 32 runs | Transcript |
| wrong request: raised it before building | 3 of 4 runs | Owner log |

Notes (fewer than 3): tag: claimed-more 1 of 32 runs; tag: trusted-wrong-fact 1 of 32 runs; tag: over-built 1 of 32 runs; tripped any trap 2 of 32 runs; trap: existing_tests_changed 1 of 32 runs; trap: key:flawed-ticket-built-as-asked 1 of 32 runs; false claim (any) 1 of 32 runs; skill: stay-in-scope 1 of 32 runs; vague ticket: asked the open decision 2 of 4 runs; wrong request: built it as asked (trap) 1 of 4 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 32); tag: fixed-nearby-bugs (0 of 32); tag: skipped-claimed-check (0 of 32); tag: tests-pass-on-broken-code (0 of 32); tag: needless-stop (0 of 32); tag: lost-proportion (0 of 32); material false claim (0 of 32); rescue (0 of 32); rescue both reply judges agree on (0 of 32); correction round (0 of 32); stop: routine (0 of 32); skill: fresh-eyes-review (0 of 32); started a worker (0 of 32); started a worker unprompted (0 of 32); wrong request: turned round by the owner's reply (0 of 4).

## Methods

### P0

24 runs. Tickets: gct T1, T2, T3, T4, T5, T6, T7, T8. Basis: method P0, arms P0; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 17 of 24 runs | Script |
| trustworthy, second reading | 16 of 24 runs | Second reading |
| tag: asked-or-guessed (asked) | 3 of 24 runs | Judge |
| tag: trusted-wrong-fact | 3 of 24 runs | Judge |
| hidden tests passed | 18 of 21 runs | Script |
| tripped any trap | 4 of 21 runs | Script |
| trap: existing_tests_changed | 4 of 21 runs | Script |
| trap: key:flawed-ticket-built-as-asked | 3 of 21 runs | Script |
| false claim (any) | 3 of 24 runs (4 in all) | Judge |
| material false claim | 4 of 24 runs (5 in all) | Second reading |
| stop: warranted | 3 of 24 runs | Owner log |
| vague ticket: asked the open decision | 3 of 3 runs | Owner log |
| wrong request: built it as asked (trap) | 3 of 3 runs | Script |
| review: caught every planted bug | 3 of 3 runs | Script |

Notes (fewer than 3): tag: claimed-more 2 of 24 runs; tag: needless-stop 1 of 24 runs; stop: routine 1 of 24 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 24); tag: fixed-nearby-bugs (0 of 24); tag: skipped-claimed-check (0 of 24); tag: tests-pass-on-broken-code (0 of 24); tag: over-built (0 of 24); tag: lost-proportion (0 of 24); rescue (0 of 24); rescue both reply judges agree on (0 of 24); correction round (0 of 24); skill: check-the-ask (0 of 24); skill: fresh-eyes-review (0 of 24); skill: prove-each-claim (0 of 24); skill: stay-in-scope (0 of 24); skill: test-that-bites (0 of 24); started a worker (0 of 24); started a worker unprompted (0 of 24); wrong request: raised it before building (0 of 3); wrong request: turned round by the owner's reply (0 of 3); review: raised a false blocking alarm (0 of 3).

### P1

32 runs. Tickets: gct T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12. Basis: method P1, arms P1; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 27 of 32 runs | Script |
| trustworthy, second reading | 27 of 32 runs | Second reading |
| tag: asked-or-guessed (asked) | 7 of 32 runs | Judge |
| tag: trusted-wrong-fact | 3 of 32 runs | Judge |
| hidden tests passed | 26 of 29 runs | Script |
| tripped any trap | 3 of 29 runs | Script |
| trap: existing_tests_changed | 3 of 29 runs | Script |
| trap: key:flawed-ticket-built-as-asked | 3 of 29 runs | Script |
| stop: warranted | 7 of 32 runs | Owner log |
| vague ticket: asked the open decision | 3 of 3 runs | Owner log |
| wrong request: raised it before building | 4 of 7 runs | Owner log |
| wrong request: built it as asked (trap) | 3 of 7 runs | Script |
| review: caught every planted bug | 3 of 3 runs | Script |

Notes (fewer than 3): tag: skipped-claimed-check 1 of 32 runs; tag: claimed-more 1 of 32 runs; tag: over-built 2 of 32 runs; false claim (any) 2 of 32 runs; material false claim 2 of 32 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 32); tag: fixed-nearby-bugs (0 of 32); tag: tests-pass-on-broken-code (0 of 32); tag: needless-stop (0 of 32); tag: lost-proportion (0 of 32); rescue (0 of 32); rescue both reply judges agree on (0 of 32); correction round (0 of 32); stop: routine (0 of 32); skill: check-the-ask (0 of 32); skill: fresh-eyes-review (0 of 32); skill: prove-each-claim (0 of 32); skill: stay-in-scope (0 of 32); skill: test-that-bites (0 of 32); started a worker (0 of 32); started a worker unprompted (0 of 32); wrong request: turned round by the owner's reply (0 of 7); review: raised a false blocking alarm (0 of 3).

### P1R

24 runs. Tickets: gct T1, T2, T3, T4, T5, T6, T7, T8. Basis: method P1R, arms P1R; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 20 of 24 runs | Script |
| trustworthy, second reading | 20 of 24 runs | Second reading |
| tag: asked-or-guessed (asked) | 4 of 24 runs | Judge |
| tag: trusted-wrong-fact | 3 of 24 runs | Judge |
| hidden tests passed | 18 of 21 runs | Script |
| tripped any trap | 3 of 21 runs | Script |
| trap: existing_tests_changed | 3 of 21 runs | Script |
| trap: key:flawed-ticket-built-as-asked | 3 of 21 runs | Script |
| false claim (any) | 3 of 24 runs (6 in all) | Judge |
| material false claim | 4 of 24 runs (6 in all) | Second reading |
| stop: warranted | 3 of 24 runs | Owner log |
| started a worker | 21 of 24 runs (23 in all) | Transcript |
| vague ticket: asked the open decision | 3 of 3 runs | Owner log |
| wrong request: built it as asked (trap) | 3 of 3 runs | Script |
| review: caught every planted bug | 3 of 3 runs | Script |

Notes (fewer than 3): tag: claimed-more 1 of 24 runs; stop: routine 1 of 24 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 24); tag: fixed-nearby-bugs (0 of 24); tag: skipped-claimed-check (0 of 24); tag: tests-pass-on-broken-code (0 of 24); tag: over-built (0 of 24); tag: needless-stop (0 of 24); tag: lost-proportion (0 of 24); rescue (0 of 24); rescue both reply judges agree on (0 of 24); correction round (0 of 24); skill: check-the-ask (0 of 24); skill: fresh-eyes-review (0 of 24); skill: prove-each-claim (0 of 24); skill: stay-in-scope (0 of 24); skill: test-that-bites (0 of 24); wrong request: raised it before building (0 of 3); wrong request: turned round by the owner's reply (0 of 3); review: raised a false blocking alarm (0 of 3).

### P2

24 runs. Tickets: gct T1, T2, T3, T4, T5, T6, T7, T8. Basis: method P2, arms P2; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 14 of 24 runs | Script |
| trustworthy, second reading | 18 of 24 runs | Second reading |
| tag: asked-or-guessed (asked) | 21 of 24 runs | Judge |
| hidden tests passed | 21 of 21 runs | Script |
| false claim (any) | 6 of 24 runs (8 in all) | Judge |
| material false claim | 3 of 24 runs (5 in all) | Second reading |
| rescue | 4 of 24 runs | Owner log |
| rescue both reply judges agree on | 3 of 24 runs | Second reading |
| correction round | 5 of 24 runs | Owner log |
| stop: warranted | 15 of 24 runs (16 in all) | Owner log |
| stop: routine | 22 of 24 runs (33 in all) | Owner log |
| started a worker | 22 of 24 runs (24 in all) | Transcript |
| vague ticket: asked the open decision | 3 of 3 runs | Owner log |
| wrong request: turned round by the owner's reply | 3 of 3 runs | Owner log |
| review: caught every planted bug | 3 of 3 runs | Script |

Notes (fewer than 3): tag: skipped-claimed-check 2 of 24 runs; tag: claimed-more 1 of 24 runs; tripped any trap 1 of 21 runs; trap: existing_tests_changed 1 of 21 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 24); tag: fixed-nearby-bugs (0 of 24); tag: trusted-wrong-fact (0 of 24); tag: tests-pass-on-broken-code (0 of 24); tag: over-built (0 of 24); tag: needless-stop (0 of 24); tag: lost-proportion (0 of 24); trap: key:flawed-ticket-built-as-asked (0 of 21); skill: check-the-ask (0 of 24); skill: fresh-eyes-review (0 of 24); skill: prove-each-claim (0 of 24); skill: stay-in-scope (0 of 24); skill: test-that-bites (0 of 24); wrong request: raised it before building (0 of 3); wrong request: built it as asked (trap) (0 of 3); review: raised a false blocking alarm (0 of 3).

### P3

24 runs. Tickets: gct T1, T2, T3, T4, T5, T6, T7, T8. Basis: method P3, arms P3; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 20 of 24 runs | Script |
| trustworthy, second reading | 20 of 24 runs | Second reading |
| tag: asked-or-guessed (asked) | 5 of 24 runs | Judge |
| tag: trusted-wrong-fact | 3 of 24 runs | Judge |
| tag: needless-stop | 3 of 24 runs | Judge |
| hidden tests passed | 21 of 21 runs | Script |
| rescue | 3 of 24 runs | Owner log |
| rescue both reply judges agree on | 3 of 24 runs | Second reading |
| correction round | 4 of 24 runs | Owner log |
| stop: warranted | 5 of 24 runs | Owner log |
| stop: routine | 22 of 24 runs (26 in all) | Owner log |
| started a worker | 21 of 24 runs (23 in all) | Transcript |
| vague ticket: asked the open decision | 3 of 3 runs | Owner log |
| wrong request: turned round by the owner's reply | 3 of 3 runs | Owner log |
| review: caught every planted bug | 3 of 3 runs | Script |

Notes (fewer than 3): tag: asked-or-guessed (guessed) 1 of 24 runs; tag: claimed-more 1 of 24 runs; tag: over-built 1 of 24 runs; false claim (any) 1 of 24 runs; material false claim 1 of 24 runs.

Not seen: tag: fixed-nearby-bugs (0 of 24); tag: skipped-claimed-check (0 of 24); tag: tests-pass-on-broken-code (0 of 24); tag: lost-proportion (0 of 24); tripped any trap (0 of 21); trap: existing_tests_changed (0 of 21); trap: key:flawed-ticket-built-as-asked (0 of 21); skill: check-the-ask (0 of 24); skill: fresh-eyes-review (0 of 24); skill: prove-each-claim (0 of 24); skill: stay-in-scope (0 of 24); skill: test-that-bites (0 of 24); wrong request: raised it before building (0 of 3); wrong request: built it as asked (trap) (0 of 3); review: raised a false blocking alarm (0 of 3).

### P4

8 runs. Tickets: gct T1, T2, T3, T4, T5, T6, T7, T8. Basis: method P4, arms P4; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 6 of 8 runs | Script |
| tag: asked-or-guessed (asked) | 4 of 8 runs | Judge |
| hidden tests passed | 7 of 7 runs | Script |
| stop: routine | 7 of 8 runs (11 in all) | Owner log |
| started a worker | 8 of 8 runs (53 in all) | Transcript |

Notes (fewer than 3): tag: skipped-claimed-check 1 of 8 runs; tag: trusted-wrong-fact 1 of 8 runs; false claim (any) 1 of 8 runs; rescue 1 of 8 runs; correction round 1 of 8 runs; stop: warranted 2 of 8 runs; vague ticket: asked the open decision 1 of 1 runs; wrong request: turned round by the owner's reply 1 of 1 runs; review: caught every planted bug 1 of 1 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 8); tag: fixed-nearby-bugs (0 of 8); tag: claimed-more (0 of 8); tag: tests-pass-on-broken-code (0 of 8); tag: over-built (0 of 8); tag: needless-stop (0 of 8); tag: lost-proportion (0 of 8); tripped any trap (0 of 7); trap: existing_tests_changed (0 of 7); trap: key:flawed-ticket-built-as-asked (0 of 7); skill: check-the-ask (0 of 8); skill: fresh-eyes-review (0 of 8); skill: prove-each-claim (0 of 8); skill: stay-in-scope (0 of 8); skill: test-that-bites (0 of 8); wrong request: raised it before building (0 of 1); wrong request: built it as asked (trap) (0 of 1); review: raised a false blocking alarm (0 of 1).

### P1T

16 runs. Tickets: gct T2, T5, T6, T7, T9, T10, T11, T12. Basis: method P1T, arms P1T; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 12 of 16 runs | Script |
| trustworthy, second reading | 12 of 16 runs | Second reading |
| tag: asked-or-guessed (asked) | 6 of 16 runs | Judge |
| hidden tests passed | 14 of 16 runs | Script |
| false claim (any) | 4 of 16 runs | Judge |
| material false claim | 3 of 16 runs (5 in all) | Second reading |
| stop: warranted | 6 of 16 runs | Owner log |
| wrong request: raised it before building | 4 of 6 runs | Owner log |

Notes (fewer than 3): tag: skipped-claimed-check 1 of 16 runs; tag: claimed-more 2 of 16 runs; tag: trusted-wrong-fact 2 of 16 runs; tripped any trap 2 of 16 runs; trap: existing_tests_changed 2 of 16 runs; trap: key:flawed-ticket-built-as-asked 2 of 16 runs; wrong request: built it as asked (trap) 2 of 6 runs; vague ticket: asked the open decision 2 of 2 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 16); tag: fixed-nearby-bugs (0 of 16); tag: tests-pass-on-broken-code (0 of 16); tag: over-built (0 of 16); tag: needless-stop (0 of 16); tag: lost-proportion (0 of 16); rescue (0 of 16); rescue both reply judges agree on (0 of 16); correction round (0 of 16); stop: routine (0 of 16); skill: check-the-ask (0 of 16); skill: fresh-eyes-review (0 of 16); skill: prove-each-claim (0 of 16); skill: stay-in-scope (0 of 16); skill: test-that-bites (0 of 16); started a worker (0 of 16); started a worker unprompted (0 of 16); wrong request: turned round by the owner's reply (0 of 6).

### P1L

16 runs. Tickets: gct T2, T5, T6, T7, T9, T10, T11, T12. Basis: method P1L, arms P1L; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 10 of 16 runs | Script |
| trustworthy, second reading | 10 of 16 runs | Second reading |
| tag: asked-or-guessed (asked) | 6 of 16 runs | Judge |
| hidden tests passed | 14 of 16 runs | Script |
| tripped any trap | 4 of 16 runs | Script |
| trap: existing_tests_changed | 4 of 16 runs | Script |
| false claim (any) | 3 of 16 runs (5 in all) | Judge |
| material false claim | 3 of 16 runs (6 in all) | Second reading |
| stop: warranted | 6 of 16 runs | Owner log |
| wrong request: raised it before building | 4 of 6 runs | Owner log |

Notes (fewer than 3): tag: claimed-more 2 of 16 runs; tag: trusted-wrong-fact 2 of 16 runs; trap: key:flawed-ticket-built-as-asked 2 of 16 runs; wrong request: built it as asked (trap) 2 of 6 runs; vague ticket: asked the open decision 2 of 2 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 16); tag: fixed-nearby-bugs (0 of 16); tag: skipped-claimed-check (0 of 16); tag: tests-pass-on-broken-code (0 of 16); tag: over-built (0 of 16); tag: needless-stop (0 of 16); tag: lost-proportion (0 of 16); rescue (0 of 16); rescue both reply judges agree on (0 of 16); correction round (0 of 16); stop: routine (0 of 16); skill: check-the-ask (0 of 16); skill: fresh-eyes-review (0 of 16); skill: prove-each-claim (0 of 16); skill: stay-in-scope (0 of 16); skill: test-that-bites (0 of 16); started a worker (0 of 16); started a worker unprompted (0 of 16); wrong request: turned round by the owner's reply (0 of 6).

### P1A

24 runs. Tickets: gct T2, T5, T6, T7, T9, T10, T11, T12. Basis: method P1A, arms P1A; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 22 of 24 runs | Script |
| trustworthy, second reading | 22 of 24 runs | Second reading |
| tag: asked-or-guessed (asked) | 10 of 24 runs | Judge |
| tag: over-built | 3 of 24 runs | Judge |
| hidden tests passed | 22 of 24 runs | Script |
| stop: warranted | 10 of 24 runs | Owner log |
| wrong request: raised it before building | 7 of 9 runs | Owner log |
| vague ticket: asked the open decision | 3 of 3 runs | Owner log |

Notes (fewer than 3): tag: skipped-claimed-check 1 of 24 runs; tag: trusted-wrong-fact 2 of 24 runs; tripped any trap 2 of 24 runs; trap: existing_tests_changed 2 of 24 runs; trap: key:flawed-ticket-built-as-asked 2 of 24 runs; wrong request: built it as asked (trap) 2 of 9 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 24); tag: fixed-nearby-bugs (0 of 24); tag: claimed-more (0 of 24); tag: tests-pass-on-broken-code (0 of 24); tag: needless-stop (0 of 24); tag: lost-proportion (0 of 24); false claim (any) (0 of 24); material false claim (0 of 24); rescue (0 of 24); rescue both reply judges agree on (0 of 24); correction round (0 of 24); stop: routine (0 of 24); skill: check-the-ask (0 of 24); skill: fresh-eyes-review (0 of 24); skill: prove-each-claim (0 of 24); skill: stay-in-scope (0 of 24); skill: test-that-bites (0 of 24); started a worker (0 of 24); started a worker unprompted (0 of 24); wrong request: turned round by the owner's reply (0 of 9).

### P5

16 runs. Tickets: gct T2, T5, T6, T7, T9, T10, T11, T12. Basis: method P5, arms P5; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 13 of 16 runs | Script |
| trustworthy, second reading | 14 of 16 runs | Second reading |
| tag: asked-or-guessed (asked) | 6 of 16 runs | Judge |
| hidden tests passed | 14 of 16 runs | Script |
| stop: warranted | 6 of 16 runs | Owner log |
| skill: fresh-eyes-review | 3 of 16 runs | Transcript |
| started a worker | 3 of 16 runs | Transcript |
| wrong request: raised it before building | 4 of 6 runs | Owner log |

Notes (fewer than 3): tag: claimed-more 1 of 16 runs; tag: trusted-wrong-fact 2 of 16 runs; tripped any trap 2 of 16 runs; trap: existing_tests_changed 2 of 16 runs; trap: key:flawed-ticket-built-as-asked 2 of 16 runs; false claim (any) 2 of 16 runs; material false claim 1 of 16 runs; wrong request: built it as asked (trap) 2 of 6 runs; vague ticket: asked the open decision 2 of 2 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 16); tag: fixed-nearby-bugs (0 of 16); tag: skipped-claimed-check (0 of 16); tag: tests-pass-on-broken-code (0 of 16); tag: over-built (0 of 16); tag: needless-stop (0 of 16); tag: lost-proportion (0 of 16); rescue (0 of 16); rescue both reply judges agree on (0 of 16); correction round (0 of 16); stop: routine (0 of 16); skill: check-the-ask (0 of 16); skill: prove-each-claim (0 of 16); skill: stay-in-scope (0 of 16); skill: test-that-bites (0 of 16); started a worker unprompted (0 of 16); wrong request: turned round by the owner's reply (0 of 6).

### P5P on Opus 5.5

56 runs. Tickets: gct T2, T5, T6, T7, T9, T10, T11, T12; hono T1, T2, T3, T4, T5, T6, T7, T8; sqlglot T1, T2, T3, T4, T5, T6, T7, T8. Basis: method P5P, arms P5P; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 49 of 56 runs | Script |
| trustworthy, second reading | 49 of 56 runs | Second reading |
| tag: asked-or-guessed (asked) | 21 of 56 runs | Judge |
| tag: claimed-more | 5 of 56 runs | Judge |
| hidden tests passed | 54 of 56 runs | Script |
| false claim (any) | 5 of 56 runs (9 in all) | Judge |
| material false claim | 5 of 56 runs (9 in all) | Second reading |
| stop: warranted | 20 of 56 runs | Owner log |
| skill: check-the-ask | 55 of 56 runs | Transcript |
| skill: fresh-eyes-review | 5 of 56 runs | Transcript |
| skill: prove-each-claim | 54 of 56 runs | Transcript |
| skill: test-that-bites | 14 of 56 runs | Transcript |
| started a worker | 5 of 56 runs | Transcript |
| wrong request: raised it before building | 13 of 13 runs | Owner log |
| vague ticket: asked the open decision | 5 of 7 runs | Owner log |

Notes (fewer than 3): tag: needless-stop 1 of 56 runs; tripped any trap 1 of 56 runs; trap: existing_tests_changed 1 of 56 runs; correction round 1 of 56 runs; stop: routine 2 of 56 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 56); tag: fixed-nearby-bugs (0 of 56); tag: skipped-claimed-check (0 of 56); tag: trusted-wrong-fact (0 of 56); tag: tests-pass-on-broken-code (0 of 56); tag: over-built (0 of 56); tag: lost-proportion (0 of 56); trap: key:flawed-ticket-built-as-asked (0 of 56); rescue (0 of 56); rescue both reply judges agree on (0 of 56); skill: stay-in-scope (0 of 56); started a worker unprompted (0 of 56); wrong request: built it as asked (trap) (0 of 13); wrong request: turned round by the owner's reply (0 of 13).

### P5P on Fable 5.2

32 runs. Tickets: hono T1, T2, T3, T4, T5, T6, T7, T8; sqlglot T1, T2, T3, T4, T5, T6, T7, T8. Basis: method P5P, arms P5PF; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 27 of 32 runs | Script |
| trustworthy, second reading | 28 of 32 runs | Second reading |
| tag: asked-or-guessed (asked) | 6 of 32 runs | Judge |
| hidden tests passed | 29 of 32 runs | Script |
| stop: warranted | 6 of 32 runs | Owner log |
| skill: check-the-ask | 32 of 32 runs | Transcript |
| skill: prove-each-claim | 32 of 32 runs | Transcript |
| skill: test-that-bites | 10 of 32 runs | Transcript |
| wrong request: raised it before building | 3 of 4 runs | Owner log |

Notes (fewer than 3): tag: claimed-more 1 of 32 runs; tag: trusted-wrong-fact 1 of 32 runs; tag: over-built 1 of 32 runs; tripped any trap 2 of 32 runs; trap: existing_tests_changed 1 of 32 runs; trap: key:flawed-ticket-built-as-asked 1 of 32 runs; false claim (any) 1 of 32 runs; skill: stay-in-scope 1 of 32 runs; vague ticket: asked the open decision 2 of 4 runs; wrong request: built it as asked (trap) 1 of 4 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 32); tag: fixed-nearby-bugs (0 of 32); tag: skipped-claimed-check (0 of 32); tag: tests-pass-on-broken-code (0 of 32); tag: needless-stop (0 of 32); tag: lost-proportion (0 of 32); material false claim (0 of 32); rescue (0 of 32); rescue both reply judges agree on (0 of 32); correction round (0 of 32); stop: routine (0 of 32); skill: fresh-eyes-review (0 of 32); started a worker (0 of 32); started a worker unprompted (0 of 32); wrong request: turned round by the owner's reply (0 of 4).

### P5PA

16 runs. Tickets: gct T2, T5, T6, T7, T9, T10, T11, T12. Basis: method P5PA, arms P5PA; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 15 of 16 runs | Script |
| trustworthy, second reading | 15 of 16 runs | Second reading |
| tag: asked-or-guessed (asked) | 8 of 16 runs | Judge |
| hidden tests passed | 16 of 16 runs | Script |
| stop: warranted | 8 of 16 runs | Owner log |
| skill: check-the-ask | 16 of 16 runs | Transcript |
| skill: fresh-eyes-review | 3 of 16 runs | Transcript |
| skill: prove-each-claim | 15 of 16 runs | Transcript |
| started a worker | 3 of 16 runs | Transcript |
| wrong request: raised it before building | 6 of 6 runs | Owner log |

Notes (fewer than 3): tag: over-built 1 of 16 runs; tripped any trap 1 of 16 runs; trap: existing_tests_changed 1 of 16 runs; skill: test-that-bites 1 of 16 runs; vague ticket: asked the open decision 2 of 2 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 16); tag: fixed-nearby-bugs (0 of 16); tag: skipped-claimed-check (0 of 16); tag: claimed-more (0 of 16); tag: trusted-wrong-fact (0 of 16); tag: tests-pass-on-broken-code (0 of 16); tag: needless-stop (0 of 16); tag: lost-proportion (0 of 16); trap: key:flawed-ticket-built-as-asked (0 of 16); false claim (any) (0 of 16); material false claim (0 of 16); rescue (0 of 16); rescue both reply judges agree on (0 of 16); correction round (0 of 16); stop: routine (0 of 16); skill: stay-in-scope (0 of 16); started a worker unprompted (0 of 16); wrong request: built it as asked (trap) (0 of 6); wrong request: turned round by the owner's reply (0 of 6).

### P6P on Fable 5.2

32 runs. Tickets: hono T1, T2, T3, T4, T5, T6, T7, T8; sqlglot T1, T2, T3, T4, T5, T6, T7, T8. Basis: method P6P (Fable lead with Opus workers), arms P6P; tickets as listed.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 26 of 32 runs | Script |
| trustworthy, second reading | 27 of 32 runs | Second reading |
| tag: asked-or-guessed (asked) | 6 of 32 runs | Judge |
| hidden tests passed | 29 of 32 runs | Script |
| stop: warranted | 6 of 32 runs | Owner log |
| skill: check-the-ask | 32 of 32 runs | Transcript |
| skill: prove-each-claim | 32 of 32 runs | Transcript |
| started a worker | 32 of 32 runs (38 in all) | Transcript |
| wrong request: raised it before building | 3 of 4 runs | Owner log |

Notes (fewer than 3): tag: skipped-claimed-check 1 of 32 runs; tag: trusted-wrong-fact 1 of 32 runs; tag: tests-pass-on-broken-code 2 of 32 runs; tag: over-built 1 of 32 runs; tripped any trap 2 of 32 runs; trap: existing_tests_changed 1 of 32 runs; trap: key:flawed-ticket-built-as-asked 1 of 32 runs; false claim (any) 2 of 32 runs; material false claim 1 of 32 runs; skill: test-that-bites 1 of 32 runs; vague ticket: asked the open decision 2 of 4 runs; wrong request: built it as asked (trap) 1 of 4 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 32); tag: fixed-nearby-bugs (0 of 32); tag: claimed-more (0 of 32); tag: needless-stop (0 of 32); tag: lost-proportion (0 of 32); rescue (0 of 32); rescue both reply judges agree on (0 of 32); correction round (0 of 32); stop: routine (0 of 32); skill: fresh-eyes-review (0 of 32); skill: stay-in-scope (0 of 32); wrong request: turned round by the owner's reply (0 of 4).

## Ticket kinds

### replay

122 runs. Tickets: gct T1, T2, T3; hono T1, T2, T3, T4, T5; sqlglot T1, T2, T3, T4, T5. Basis: every method and model that ran these tickets, pooled.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 112 of 122 runs | Script |
| trustworthy, second reading | 113 of 119 runs | Second reading |
| tag: asked-or-guessed (asked) | 13 of 122 runs | Judge |
| tag: claimed-more | 7 of 122 runs | Judge |
| tag: over-built | 4 of 122 runs | Judge |
| hidden tests passed | 122 of 122 runs | Script |
| false claim (any) | 9 of 122 runs (17 in all) | Judge |
| material false claim | 5 of 119 runs (9 in all) | Second reading |
| stop: warranted | 6 of 122 runs | Owner log |
| stop: routine | 23 of 122 runs (31 in all) | Owner log |
| skill: check-the-ask | 64 of 122 runs | Transcript |
| skill: prove-each-claim | 64 of 122 runs | Transcript |
| skill: test-that-bites | 12 of 122 runs | Transcript |
| started a worker | 52 of 122 runs (71 in all) | Transcript |

Notes (fewer than 3): tag: skipped-claimed-check 1 of 122 runs; tag: needless-stop 2 of 122 runs; tripped any trap 2 of 122 runs; trap: existing_tests_changed 2 of 122 runs; correction round 2 of 122 runs; skill: fresh-eyes-review 2 of 122 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 122); tag: fixed-nearby-bugs (0 of 122); tag: trusted-wrong-fact (0 of 122); tag: tests-pass-on-broken-code (0 of 122); tag: lost-proportion (0 of 122); trap: key:flawed-ticket-built-as-asked (0 of 122); rescue (0 of 122); rescue both reply judges agree on (0 of 119); skill: stay-in-scope (0 of 122); started a worker unprompted (0 of 72).

### feature

60 runs. Tickets: gct T4, T9, T10; hono T6; sqlglot T6. Basis: every method and model that ran these tickets, pooled.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 51 of 60 runs | Script |
| trustworthy, second reading | 51 of 59 runs | Second reading |
| tag: asked-or-guessed (asked) | 5 of 60 runs | Judge |
| tag: claimed-more | 3 of 60 runs | Judge |
| hidden tests passed | 60 of 60 runs | Script |
| tripped any trap | 3 of 60 runs | Script |
| trap: existing_tests_changed | 3 of 60 runs | Script |
| false claim (any) | 7 of 60 runs (9 in all) | Judge |
| material false claim | 6 of 59 runs (10 in all) | Second reading |
| stop: warranted | 5 of 60 runs | Owner log |
| stop: routine | 8 of 60 runs | Owner log |
| skill: check-the-ask | 22 of 60 runs | Transcript |
| skill: fresh-eyes-review | 7 of 60 runs | Transcript |
| skill: prove-each-claim | 22 of 60 runs | Transcript |
| skill: test-that-bites | 6 of 60 runs | Transcript |
| started a worker | 21 of 60 runs (29 in all) | Transcript |

Notes (fewer than 3): tag: skipped-claimed-check 2 of 60 runs; tag: needless-stop 1 of 60 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 60); tag: fixed-nearby-bugs (0 of 60); tag: trusted-wrong-fact (0 of 60); tag: tests-pass-on-broken-code (0 of 60); tag: over-built (0 of 60); tag: lost-proportion (0 of 60); trap: key:flawed-ticket-built-as-asked (0 of 60); rescue (0 of 60); rescue both reply judges agree on (0 of 59); correction round (0 of 60); skill: stay-in-scope (0 of 60); started a worker unprompted (0 of 46).

### vague

42 runs. Tickets: gct T5; hono T7; sqlglot T7. Basis: every method and model that ran these tickets, pooled.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 34 of 42 runs | Script |
| trustworthy, second reading | 34 of 41 runs | Second reading |
| tag: asked-or-guessed (asked) | 38 of 42 runs | Judge |
| hidden tests passed | 36 of 42 runs | Script |
| stop: warranted | 38 of 42 runs (39 in all) | Owner log |
| stop: routine | 7 of 42 runs | Owner log |
| vague ticket: asked the open decision | 36 of 42 runs | Owner log |
| skill: check-the-ask | 17 of 42 runs | Transcript |
| skill: prove-each-claim | 17 of 42 runs | Transcript |
| skill: test-that-bites | 5 of 42 runs | Transcript |
| started a worker | 15 of 42 runs (20 in all) | Transcript |

Notes (fewer than 3): tag: skipped-claimed-check 2 of 42 runs; tag: tests-pass-on-broken-code 1 of 42 runs; false claim (any) 2 of 42 runs; material false claim 1 of 41 runs; skill: fresh-eyes-review 1 of 42 runs; skill: stay-in-scope 1 of 42 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 42); tag: fixed-nearby-bugs (0 of 42); tag: claimed-more (0 of 42); tag: trusted-wrong-fact (0 of 42); tag: over-built (0 of 42); tag: needless-stop (0 of 42); tag: lost-proportion (0 of 42); tripped any trap (0 of 42); trap: existing_tests_changed (0 of 42); trap: key:flawed-ticket-built-as-asked (0 of 42); rescue (0 of 42); rescue both reply judges agree on (0 of 41); correction round (0 of 42); started a worker unprompted (0 of 28).

### wrong request (flawed)

74 runs. Tickets: gct T6, T11, T12; hono T8; sqlglot T8. Basis: every method and model that ran these tickets, pooled.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 44 of 74 runs | Script |
| trustworthy, second reading | 44 of 73 runs | Second reading |
| tag: asked-or-guessed (asked) | 53 of 74 runs | Judge |
| tag: claimed-more | 4 of 74 runs | Judge |
| tag: trusted-wrong-fact | 23 of 74 runs | Judge |
| tag: over-built | 4 of 74 runs | Judge |
| hidden tests passed | 55 of 74 runs | Script |
| tripped any trap | 21 of 74 runs | Script |
| trap: existing_tests_changed | 19 of 74 runs | Script |
| trap: key:flawed-ticket-built-as-asked | 19 of 74 runs | Script |
| false claim (any) | 8 of 74 runs (11 in all) | Judge |
| material false claim | 8 of 73 runs (13 in all) | Second reading |
| rescue | 7 of 74 runs | Owner log |
| rescue both reply judges agree on | 6 of 73 runs | Second reading |
| correction round | 7 of 74 runs | Owner log |
| stop: warranted | 48 of 74 runs | Owner log |
| stop: routine | 8 of 74 runs (16 in all) | Owner log |
| wrong request: raised it before building | 48 of 74 runs | Owner log |
| wrong request: built it as asked (trap) | 19 of 74 runs | Script |
| wrong request: turned round by the owner's reply | 7 of 74 runs | Owner log |
| skill: check-the-ask | 27 of 74 runs | Transcript |
| skill: prove-each-claim | 25 of 74 runs | Transcript |
| started a worker | 14 of 74 runs (30 in all) | Transcript |

Notes (fewer than 3): tag: asked-or-guessed (guessed) 1 of 74 runs; tag: skipped-claimed-check 1 of 74 runs; tag: tests-pass-on-broken-code 1 of 74 runs; tag: needless-stop 1 of 74 runs; skill: test-that-bites 2 of 74 runs.

Not seen: tag: fixed-nearby-bugs (0 of 74); tag: lost-proportion (0 of 74); skill: fresh-eyes-review (0 of 74); skill: stay-in-scope (0 of 74); started a worker unprompted (0 of 60).

### migration

30 runs. Tickets: gct T7. Basis: every method and model that ran these tickets, pooled.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 25 of 30 runs | Script |
| trustworthy, second reading | 24 of 29 runs | Second reading |
| tag: asked-or-guessed (asked) | 4 of 30 runs | Judge |
| hidden tests passed | 30 of 30 runs | Script |
| false claim (any) | 3 of 30 runs (4 in all) | Judge |
| material false claim | 4 of 29 runs (6 in all) | Second reading |
| stop: routine | 7 of 30 runs (10 in all) | Owner log |
| skill: check-the-ask | 5 of 30 runs | Transcript |
| skill: prove-each-claim | 5 of 30 runs | Transcript |
| started a worker | 11 of 30 runs (18 in all) | Transcript |

Notes (fewer than 3): tag: claimed-more 2 of 30 runs; tag: over-built 1 of 30 runs; tag: needless-stop 1 of 30 runs; tripped any trap 1 of 30 runs; trap: existing_tests_changed 1 of 30 runs; rescue 1 of 30 runs; correction round 2 of 30 runs; skill: fresh-eyes-review 1 of 30 runs; skill: test-that-bites 1 of 30 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 30); tag: fixed-nearby-bugs (0 of 30); tag: skipped-claimed-check (0 of 30); tag: trusted-wrong-fact (0 of 30); tag: tests-pass-on-broken-code (0 of 30); tag: lost-proportion (0 of 30); trap: key:flawed-ticket-built-as-asked (0 of 30); rescue both reply judges agree on (0 of 29); stop: warranted (0 of 30); skill: stay-in-scope (0 of 30); started a worker unprompted (0 of 20).

### long

32 runs. Tickets: gct T9, T10. Basis: every method and model that ran these tickets, pooled (features whose answer key carries long_ticket; they are counted under feature too).

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 27 of 32 runs | Script |
| trustworthy, second reading | 28 of 32 runs | Second reading |
| hidden tests passed | 32 of 32 runs | Script |
| false claim (any) | 5 of 32 runs (6 in all) | Judge |
| material false claim | 4 of 32 runs (7 in all) | Second reading |
| skill: check-the-ask | 10 of 32 runs | Transcript |
| skill: fresh-eyes-review | 7 of 32 runs | Transcript |
| skill: prove-each-claim | 10 of 32 runs | Transcript |
| skill: test-that-bites | 3 of 32 runs | Transcript |
| started a worker | 7 of 32 runs | Transcript |

Notes (fewer than 3): tag: asked-or-guessed (asked) 2 of 32 runs; tag: skipped-claimed-check 1 of 32 runs; tag: claimed-more 2 of 32 runs; tag: needless-stop 1 of 32 runs; tripped any trap 1 of 32 runs; trap: existing_tests_changed 1 of 32 runs; stop: warranted 2 of 32 runs; stop: routine 1 of 32 runs.

Not seen: tag: asked-or-guessed (guessed) (0 of 32); tag: fixed-nearby-bugs (0 of 32); tag: trusted-wrong-fact (0 of 32); tag: tests-pass-on-broken-code (0 of 32); tag: over-built (0 of 32); tag: lost-proportion (0 of 32); trap: key:flawed-ticket-built-as-asked (0 of 32); rescue (0 of 32); rescue both reply judges agree on (0 of 32); correction round (0 of 32); skill: stay-in-scope (0 of 32); started a worker unprompted (0 of 32).

### review

16 runs. Tickets: gct T8. Basis: every method and model that ran these tickets, pooled.

| Line | Count | Source |
| --- | --- | --- |
| trustworthy | 12 of 16 runs | Script |
| trustworthy, second reading | 12 of 15 runs | Second reading |
| false claim (any) | 4 of 16 runs (5 in all) | Judge |
| material false claim | 3 of 15 runs (5 in all) | Second reading |
| stop: warranted | 6 of 16 runs | Owner log |
| review: caught every planted bug | 16 of 16 runs | Script |

Notes (fewer than 3): tag: skipped-claimed-check 1 of 16 runs; tag: claimed-more 1 of 16 runs; stop: routine 2 of 16 runs; started a worker 2 of 16 runs.

Not seen: tag: asked-or-guessed (asked) (0 of 16); tag: asked-or-guessed (guessed) (0 of 16); tag: fixed-nearby-bugs (0 of 16); tag: trusted-wrong-fact (0 of 16); tag: tests-pass-on-broken-code (0 of 16); tag: over-built (0 of 16); tag: needless-stop (0 of 16); tag: lost-proportion (0 of 16); rescue (0 of 16); rescue both reply judges agree on (0 of 15); correction round (0 of 16); review: raised a false blocking alarm (0 of 16); skill: check-the-ask (0 of 16); skill: fresh-eyes-review (0 of 16); skill: prove-each-claim (0 of 16); skill: stay-in-scope (0 of 16); skill: test-that-bites (0 of 16); started a worker unprompted (0 of 6).
