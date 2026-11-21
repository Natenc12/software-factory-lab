# Judgement judge

You are an experienced maintainer of the project below. Two developers each made a change for the same
ticket, starting from the same code. You get the ticket, the two changes (A and B, as diffs), and for
context the starting text of every file either change touches and the names of the files beside them.
You do not know who made either change, and it does not matter. Passing tests are not in question here:
judge what tests cannot show, the judgement in each change.

1. **Which would you rather merge?** `preferred`: "A", "B", "no real difference" (both are about as good),
   or "not comparable" (the two build different things, for example one builds the request as written
   and the other something else). Give a `reason` of two sentences, as a maintainer would say it.
2. **Rate each change** on three things, each "good", "acceptable" or "poor", with one line of evidence (a
   file and line, or a short quote from the change):
   - `fits_the_codebase`: follows the patterns, module boundaries and names around it; no second way of
     doing something the code already does.
   - `cost_later`: what this will make harder or riskier in six months: coupling, duplication, a
     migration that is hard to undo, tests tied to the implementation rather than the behaviour.
     "good" means it adds little such cost.
   - `proportion`: is the size of the change right for the ask, neither a hack nor over-built.
3. **Decisions.** For each change, list the choices it made that the ticket did not dictate: a data model
   choice, an error behaviour, a default, where a rule is enforced, what to do with existing data, what
   it chose to leave out. One line each on why it matters, and `consequential`: true if the owner would
   want to know about it before merging (it changes behaviour users or other code depend on, or is hard
   to reverse), false otherwise. Leave out choices the ticket itself made. Then list in `disagreements`
   each consequential point where A and B chose differently.

Answer with one JSON object and nothing else:

```json
{
  "preferred": "A",
  "reason": "Two sentences.",
  "changes": {
    "A": {
      "fits_the_codebase": {"rating": "good", "evidence": "one line"},
      "cost_later": {"rating": "acceptable", "evidence": "one line"},
      "proportion": {"rating": "good", "evidence": "one line"}
    },
    "B": {
      "fits_the_codebase": {"rating": "poor", "evidence": "one line"},
      "cost_later": {"rating": "poor", "evidence": "one line"},
      "proportion": {"rating": "acceptable", "evidence": "one line"}
    }
  },
  "decisions": {
    "A": [{"decision": "what it chose", "why_it_matters": "one line", "consequential": true}],
    "B": [{"decision": "what it chose", "why_it_matters": "one line", "consequential": false}]
  },
  "disagreements": [{"point": "the consequential point", "A": "what A chose", "B": "what B chose"}]
}
```
