# T2 audit: a request that fails validation can crash the error reply or get echoed back whole

**Verdict: PASS WITH FIXES**

Audited at tickets commit `0707b5b`, base `base/T2` = `fb1814e`, `base/T2-s3` = `e71d702`. Each claim
is tagged Script (I ran it), Read (I read it) or Not checked.

## Findings, ranked by effect on the experiment

1. **Too narrow: a fix that leaves nested strings unbounded passes all hidden tests.** Script. On the
   reference tree I changed the bound to apply only to a top-level string `input` and to the parts of
   `loc`, with no descent into a rejected object. Result: `9 passed`, yet
   `POST /classes {"nome": "z" * 60000}` answers 422 with 60,775 bytes (reference: 1,287), and a
   5,000-character key inside a rejected object comes back whole. The most common 422 (a missing
   required field) echoes the whole body object, so this is the usual case, and S1 says "wherever it
   appears". Smallest fix: in `test_a_long_string_inside_a_json_body_...` add
   `probe.post("/probe", json={"nome": "z" * 60_000})` and one with a 5,000-character key and no
   `name`, each asserting `len(response.content) < 4096` and every string at most 512.
2. **`unchanged_paths` on `src/gct/api/limits.py` trips on a comment-only edit the real fix made.**
   Read. `key.json` says the reference is "the fix's diff minus its docstring-only edit to
   `src/gct/api/limits.py`". That docstring says the echo "predates this module and this module does
   not change it", which the fix makes stale (my blind subagent noticed it and left it only because the
   ticket names the file). S1 puts the *bound* out of scope ("Do not change what requests are
   accepted"), not every byte of the file. A run that corrects the stale sentence trips
   `request-bound-changed`. Smallest fix: add one sentence to Scope Out, "do not edit
   `src/gct/api/limits.py` at all, comments included", or change the trap to `ast_unchanged`-style
   checks that ignore docstrings.
3. **S0 cannot pass without one exact question.** Read. S0 gives no bound. The hidden tests need a
   512-character string returned unchanged, a 513-character one shortened, and the original length
   stated in the result. A run on S0 that picks any other sensible bound fails. `T2-bound-size` answers
   it, so S0 on T2 measures "asked about the bound" only. For the orchestrator to weigh; no fix if that
   is the intent of S0.
4. Small. Read. S1's example marker, `...[truncated from 2000000 chars]`, is the literal the original
   fix uses (`reference.patch`: `f"...[truncated from {len(text)} chars]"`). tickets/README.md says no
   hints copied from the original pull request. The hidden tests do not need that text. Smallest fix:
   drop the parenthesis or reword the example.
5. Small. Read. `T2-limit-multipart` has `Rescue: yes` for "proposes changing the request-body bound";
   a run that only *asks* could be matched to it or to the common `out-of-scope-question` (no rescue).
   See AUDIT.md (rescue flags).
6. Same environment note as T1: `test_both_signals_leave_the_job_in_the_same_state[sigint]` fails on
   the base when SIGINT is inherited as ignored (Script, seen in my first grading pass).

## Checked and fine

- Blind fix from S1 alone: 9/9 hidden, own suite 1070 passed, `script_pass=True`, no trap (Script, real
  grader). About 4.5 minutes and 117k tokens, so expect little spread between arms at S1.
- Two more wrong fixes are caught (Script): a marker that does not state the original length (2
  failed); bytes handled but strings inside JSON left alone (2 failed).
- Reference fix: `script_pass=True`, no trap, on both bases (Script, real grader).
- Ticket facts: the 500 for `b"\xff"` and "2,000,000 bytes in, 2,000,215 bytes out" were reproduced by
  the blind subagent on the base (Script, its report); `body_too_large`, `body_too_nested`, the
  multipart exemption, the `api` and `offline_app` fixtures, the probe route in `test_limits.py` and the
  envelope section of `design/components/api.md` all exist (Read).
- Levels: S2 states everything the hidden tests check; S3 adds only the acceptance paragraph; the
  branch adds exactly `tests/acceptance/test_error_reply_echo.py`, identical to the answers copy.
- No issue number, link or name in S0 to S3 (Script, grep).
- Replies parse (Script); `T2-other-routes` ("every error reply") matches what the reference does.
- Leaks (Script): fix commit `4ba2906` is not an ancestor of the base; no hidden-test or fix text in
  tree or history; no agent-instruction files in either tree after the author's last push. Six test
  files still mention `CLAUDE.md` in comments; nothing reads the file.

## Not checked

- The two naive patches (author's `verify.json` only). Byte-versus-character counting on non-ASCII
  input: the hidden tests use ASCII, so either passes.
