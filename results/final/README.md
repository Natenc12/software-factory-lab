# Final results: counted data

- `profiles.json`, `profiles.md`: model and method profiles, made by `python3 -m grader.profiles`. Each line
  is "k of n runs" with its source (Script, Judge, Second reading, Owner log, Transcript); a line with fewer
  than 3 observations is a note. Stages are read from their corrected copies (`combined2` for stages 1 to
  2b, `corrected4` for stage 4); the "Where the numbers come from" table names each.
- `questions.json`: the numbers that answer Q1 to Q6 and the cross-check, made by
  `python3 -m grader.questions` from the committed summaries. Shape:
  `{made_by, time, note, readings, gradings, questions: [{id, question, decides, rule, answer: {text, value,
  source, path, reading, grading}, numbers: [{label, value, source, path, reading, grading, derived?}]}]}`.
  `reading` is `current` (decides) or `second`; `grading` is `corrected` or `as frozen`.
- `tools/make_variant5.sh`, `tools/regrade_workers_early.sh`: copy stages 1 to 2b to
  `~/factory-runs-variants/corrected5` and judge honesty again (passes 1 and 2, severity) for the 80 runs
  with worker calls, under post-freeze correction 4. Not run; waits for the owner's word.
