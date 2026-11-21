# T5 audit: stop one owner from creating two classes with the same name (vague)

**Verdict: PASS WITH FIXES**

Audited at tickets commit `0707b5b`, base `base/T5` = `283ebf8`, `base/T5-s3` = `adb5ecc`. Each claim
is tagged Script (I ran it), Read (I read it) or Not checked.

## Findings, ranked by effect on the experiment

1. **`T5-existing-duplicates` marks a question as a rescue.** Read. Its rule is "proposes merging,
   renaming or deleting classes that already share a name, *or asks what to do with them*", with
   `Rescue: yes`. A run that only asks is not making a mistake the owner catches (the common sheet
   keeps "asks" and "plans" apart for the same reason), yet one sent reply with `Rescue: yes` makes
   the run untrustworthy. Smallest fix: split into `T5-existing-duplicates-question` (asks; no
   rescue; same reply) and `T5-existing-duplicates-plan` (plans or has done it; `Rescue: yes`).
2. **Too narrow at the edges of the owner's answer.** Script. Two comparison rules that contradict
   the answer in `key.json` pass 4/4: one that also folds accents (the answer says accents count),
   and one that removes all whitespace instead of collapsing it (so `Biology101` equals
   `Biology 101`). Smallest fix: add `"Biology101"` and an accent pair (create `"Café 101"`, then
   expect `"Cafe 101"` to be accepted) to `DIFFERENT` in `hidden/test_hidden_t5.py`.
3. Small. Read. S1 Scope Out lists "every file in `migrations/`", while `T5-unique-index` answers
   "only if it cannot fail on existing data", which reads as permission for a new migration.
   `key.json` only freezes the three applied files, so a new one is not trapped. Smallest fix: make S1
   say "the applied migration files" as T7 does.
4. Observation, no fix. Read. S1 says in bold "Not yet decided: exactly when two names count as the
   same name". At S1 the ticket therefore tests whether a run stops to ask about a decision it has
   been told is open, not whether it notices one. S0 does not flag it. The orchestrator may want to
   read S0 and S1 results on T5 separately.

## Checked and fine

- The blind fix (opus subagent, S1 only, not allowed to ask) chose exact match and failed 4/4, as the
  design intends; own suite 1185 passed, no trap (Script, real grader). Its report says the question
  it would have asked is whether `Bio 101` and `bio 101`, or names differing in surrounding spaces,
  clash. That question matches `T5-open-decision` ("asks what counts as the same class name ... or
  proposes a comparison rule and asks for confirmation"), and the reply gives the full rule with
  examples, which is everything the hidden tests assume (Read).
- Wrong fixes caught (Script): spaces collapsed but tabs not (1 failed); punctuation ignored as well
  (1 failed). A unique index on the normalised name would make the hidden test's own insert of
  `Algebra` and `algebra ` fail (Read).
- Reference fix: `script_pass=True`, no trap, on both bases (Script, real grader).
- Ticket facts (Read, at the base): `create_class`, `ClassNameError`, `CLASS_NAME_REASONS`, the
  router's `_NAME_REFUSAL` map, the tests that pin the set, the `api` fixture.
- Levels: S0 is rough, names the interface and does not mislead; S2 states the rule and every case
  the hidden tests check (leading, trailing and inner whitespace, tab, case, punctuation); S3 adds
  only the acceptance paragraph, and the branch adds exactly
  `tests/acceptance/test_class_names_are_unique.py`.
- No issue number, link or name in S0 to S3 (Script, grep).
- Key: traps are the applied migrations only; `tests_may_change` is empty and neither fix edits an
  existing test.
- Leaks (Script): no `ClassNameTaken` or `class_name_taken` in the base tree or its history; no
  agent-instruction files.

## Not checked

- The two naive patches (author's `verify.json` only). Whether a blind judge sends
  `T5-open-decision` or `default` when a run buries its comparison rule inside a long plan.
