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
- `REJUDGE.md`: stages 1 to 2b judged again under post-freeze correction 4 (worker calls labelled), on the
  copy root `~/factory-runs-variants/final`: verdicts that changed, each row before and after, whether any
  rule would have come out differently (none on the deciding reading), commands and spend.
  `rejudged/<stage>/` holds the summaries after (and `before/`), `rejudged/changes.json` the per-run detail.
- `tools/make_final_root.py`, `tools/rejudge_final.sh`, `tools/compare_rejudge.py`: build the copy root,
  judge one run again, compare before and after.
