# Untested ideas

Small additions the results suggest but no stage tested. They are **not** part of the checklist,
which is exactly what ran (arm P5P). Each would need its own test before it joins.

1. **When a ticket marks a point "not yet decided", ask, or state the choice you made.** sqlglot T7 had
   one point marked "Not yet decided": none of the six runs asked about that point (two stopped to ask
   about something else), and all six failed one hidden test of two. Hono T7 could not be built without the answer: all six asked and passed (stage 4).
2. **Count before you claim a number.** Stage 4 (corrected) had six runs with a false claim across the
   three rows; of the five outside T7 and T8, four were miscounts of tests or files.
3. **Before the report, check that no existing test changed unless the ticket asked.** Stage 4 had two
   `existing_tests_changed` trips, although `test-that-bites` already says not to edit existing tests.
4. **Treat a rule in the project's own docs as binding, even when breaking it looks minor.** On sqlglot
   T8, one Fable-alone run and one Fable-led run built the request as asked and listed the project's
   "no-dependency" wording as something left for later; both P5P runs raised it (stage 4).
