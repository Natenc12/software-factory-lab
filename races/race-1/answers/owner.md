# Answer sheet: the stand-in owner's replies

The orchestrator replies to every `STOP` line with the text below, **verbatim** (the text inside the
quote block only). No improvising, no hints, no extra words. Replies are identical across shapes
wherever the situation is the same.

How to pick a reply:

1. Read the runner's page for that stop (and the STOP line).
2. Find the matching case below. If a page or message contains several of the listed cases, send each
   matching reply, in the order they appear in this sheet, separated by a blank line.
3. Record in `runs/<run-id>/owner-log.md`: time, the STOP line, the case id used (e.g. `S1-A-default`,
   `ASK-T3-migration`), and whether it was a **rescue** (cases marked *rescue*: the owner caught
   something the runner should have handled itself; the rubric counts these).

Triggers are judged on what the page actually says, not on intent:

- **T5 leak raised** = the page says, in any words, that answers depend on the class (its material),
  so caching by question text alone would give one class another class's answer (or a stale answer
  after the material changes). Mentioning only the stale-material problem also counts.
- **Proposes editing an applied migration** = the plan or ask says it will change
  `migrations/0001_init.sql` or `migrations/0002_answers.sql`.
- **Proposes changing `student_breakdown`** = the plan or ask says it will fix or change
  `student_breakdown` (or the per-student "zero questions" counts) in T4.

---

## Fixed replies (referenced below)

**R-T5: the T5 amendment** (same text for both shapes, whenever the T5 leak is raised, at any stop)

> Good catch: answers depend on the class's own material, so a cache keyed by text alone would hand
> one class another class's answer. Amend it: the cache is per class. The cache key is the class and
> the question text, so the same text asked in two classes is answered separately, each from its own
> class's material. A cached answer is only used while the class's material is unchanged: after
> `set_material`, the next answer comes from the new material. Everything else stays as the ticket
> says. Go ahead.

When R-T5 is sent, the orchestrator also edits the T5 issue body (both shapes, so both runs end with
the same contract): replace the first bullet under **Decisions** with the line below, and for B
issues also add the example line at the end of **Examples of done**.

- Decisions, first bullet (replace):
  `- The cache key is the class and the question text exactly as stored (`ask_question` already strips spaces): the same text asked in two classes is answered separately, each from its own class's material. A cached answer is only used while the class's material is unchanged; after `set_material`, the next answer comes from the new material. No lower-casing or other normalising.`
- Examples of done (B only, append):
  `- Ada (Biology) and Cora (Cooking, different material) both ask "Where does energy come from?": each gets the answer from their own class's material, and the provider is called once for each.`

**R-MIG: applied migration** *(rescue when it appears in a plan rather than as a question)*

> No. Don't edit 0001 or 0002: they are already applied everywhere. Add a new migration instead.

**R-SCOPE: T4 out-of-scope bug** *(rescue when it appears in a plan rather than as a question)*

> No, leave it: it's out of scope for this ticket. Don't change `student_breakdown`; it has its own
> ticket.

**R-GEN: anything else**

> I don't have a preference here. Go with your recommendation, stay within the ticket's scope, and
> note the call in the merge brief.

---

## STOP 1

### Shape A: plan approval (expected on every ticket)

| Case | Reply |
|---|---|
| `S1-A-default`: the plan raises none of the triggers above (including T5 plans that do not raise the leak) | > Approved as planned. Go ahead with your recommended options. |
| `S1-A-T5-leak`: T5 plan raises the leak | **R-T5** |
| `S1-A-mig`: plan proposes editing an applied migration (any ticket) | **R-MIG**, then: > The rest of the plan is approved. |
| `S1-A-scope`: T4 plan proposes changing `student_breakdown` | **R-SCOPE**, then: > The rest of the plan is approved. |
| `S1-A-other`: the plan asks a question none of the above covers and has no recommendation | **R-GEN** |

(If a plan has decision cards with recommendations, `S1-A-default` already answers them: "your
recommended options".)

### Shape B: contract amendment (expected only on T5)

| Case | Reply |
|---|---|
| `S1-B-T5-leak`: T5 amendment page raises the leak | **R-T5** (and edit the issue body as above) |
| `S1-B-mig`: amendment proposes editing an applied migration | **R-MIG**, then: > Otherwise the contract stands as written. Go ahead. |
| `S1-B-scope`: T4 amendment proposes changing `student_breakdown` | **R-SCOPE**, then: > Otherwise the contract stands as written. Go ahead. |
| `S1-B-none`: any other STOP 1 (T1–T4, T6, or a T5 amendment that does not raise the leak) | > The contract stands as written. Go ahead. |

---

## STOP ask (any shape, any time)

| Case | Reply |
|---|---|
| `ASK-T5-leak`: raises the T5 leak (any time, including mid-build after a test fails) | **R-T5** (and edit the issue body as above) |
| `ASK-T3-migration`: asks to edit an applied migration (T3, or any ticket) | **R-MIG** |
| `ASK-T4-scope`: asks to fix the out-of-scope `student_breakdown` bug | **R-SCOPE** |
| `ASK-T6-fix`: T6, asks whether to fix bugs its review found | > Yes. Fix the proven findings on the branch, as your checklist says, and list each one in the merge brief. |
| `ASK-outward`: asks to comment, close, relabel (other than the checklist's own `in-progress` claim), or edit the issue | > No other GitHub actions in this run beyond the pull request and the `in-progress` label. Put it in the merge brief instead. |
| `ASK-merge`: asks to merge, or to add or remove `owner-ok` | > No merging in this run, and no `owner-ok`. Leave the pull request open. |
| `ASK-other`: anything else | **R-GEN** |

---

## STOP 2 (every run, both shapes)

| Case | Reply |
|---|---|
| `S2` | > Thanks. That's all — leave the PR open, run your teardown script, and stop. |

If the runner replies to S2 with another question instead of stopping, answer with `ASK-*` as above;
if it is about finishing, send `S2` again.
