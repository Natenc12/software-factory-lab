# Add-on +Interview first

**Tests:** Q6, since it moves the owner's attention to the start, like a better spec. Also Q2.
**Added to:** P0 in stage 1, as a cheap comparison with spec levels S2 and S3. Then to the best process arm in stage 2 if P0+Interview looks promising.

## Why

On vague versions of real GitHub issues, models "do not interact without an explicit prompt". Forcing a question round before work improved results by up to 74%, and Claude Sonnet 4 then reached 89% of its full-spec score. With strong prompting Sonnet 4 spotted vague tasks with 0.89 accuracy and 3% false alarms. With neutral prompting it missed 44% of them. ([Ambig-SWE](https://arxiv.org/html/2502.13069v3), read 2026-11-21.) The charter's vague ticket checks this behaviour ("guessing instead of asking").

An interview might deliver most of what S2/S3 give at lower spec cost, because the owner answers 2–4 questions instead of reading a full spec.

## What the run is given

The host arm's normal brief, plus this block at the top, word for word:

> Before you change any file, read the ticket and the code it touches. Then send ONE message with every question whose answer would change what you build. Each question gets your recommended answer, so the owner can reply "yes to all". Ask at most 5. If nothing is unclear, say "No questions" and start. After this message, ask nothing more unless you find a conflict with a test or a recorded decision.

## What changes from P0–P4

- One planned owner stop at the start. The stand-in owner answers each question from the frozen sheet, which holds the ticket's hidden intent. If the sheet has no answer, it accepts the recommendation, as the one-reply policy already says.
- No later stops, except conflicts.

## Expected extra cost

About +5–15k tokens per run for reading code before asking. Owner attention: one stop, about 100–250 words read, one reply. Count it in "total attention", as for spec cost.

## How we would know it helped

- **On the vague and flawed tickets:** P0+Interview has fewer "guessed on a vague spec" tags and fewer tripped traps than P0.
- **On the clear tickets:** "No questions" in at least 5 of 8 runs. More questions than that is noise that costs attention, scored as routine stops.
- **Against spec levels (Q6):** if P0+Interview on S1 comes within one trustworthy PR of P0 on S2, at lower total attention, the interview beats writing a fuller spec.

## Run count

Stage 1: P0+Interview on S1, 8 tickets × 3 repeats = 24 runs. If the budget is tight, run only the vague, flawed, multi-file and one replay ticket (4 × 3 = 12).
