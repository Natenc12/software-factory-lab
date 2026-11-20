# Shape A vs shape B: every intentional difference

Everything not listed here is word-for-word identical between `A/SKILL.md` and `B/SKILL.md`
(check with `diff A/SKILL.md B/SKILL.md`), including the benchmark rules block, hard rules 1, 4, 5,
steps 2–4, 8, 9 and Spikes. Both use the same `lab-up.sh` / `lab-down.sh`.

| Where | Shape A (today's checklist) | Shape B (contract first) |
|---|---|---|
| Front matter, title | "…with the owner in the loop…"; "shape A" | adds "working from the ticket's signed contract"; "shape B: contract first" |
| Intro | — | **The contract** paragraph: Examples of done, Must not change, Decisions, Scope are the source of truth; only the owner changes it |
| Hard rule 2 | Two stops always: Stop 1 plan, Stop 2 merge brief | Stop 1 only if the contract is wrong/incomplete/contradictory; Stop 2 always |
| Hard rule 3 | "Leaving the plan means stopping" (plan departures that change files, history or data) | Mandatory stop for: Must-not-change lines, out of scope, stored data/history/applied migrations. Everything else → "calls made without you" |
| Hard rule 6 | — | adds: never edit the issue body; contract changes are proposed on a page, made by the owner |
| Talking to the owner, page list | Plan (`plan.html`, Stop 1) | Contract amendment (`plan.html`, Stop 1, only when needed) |
| Step 0 Intake | Check factual claims; note what "Done when" depends on | Copy contract verbatim to `runs/<id>/contract.md`; check claims, each Example, each Must-not-change line, contradictions, unmentioned harm |
| Step 1 | Always: plan page with decision cards, `STOP 1` | Contract sound → short `plan.html` note, no stop. Contract flawed → amendment page (what's wrong, example, proposed line), `STOP 1` |
| Step 5 Prove | Run each "Done when" check | Each Example of done becomes a test (or reproducible check) that CI runs; mechanical Must-not-change checks; label per contract line |
| Step 6 reviewer input | the ticket (`gh issue view`), checks against Scope and the approved plan | the contract verbatim (not ticket prose, not builder notes; told not to open the issue), checks against every contract line |
| Step 7 brief, top | Strip, Refresher, four answers, Merge/Change/Hold | Strip, the contract with ✓/✗ + who checked beside every line (Examples, Must not change, Decisions, Scope Out), Merge/Change/Hold |
| Step 7 brief, order | `gh pr checks` facts + Builder's view first; then evidence, reviewer findings, calls made without the owner, Not checked, files, undo | calls made without you; `gh pr checks` + Builder's view; then reviewer findings, Not checked, files, undo |
| `reviewer-brief.md` | gets the ticket; 3–8 checks from "Done when"; scope/decisions | gets pasted contract, no issue; one check per Example and per Must-not-change line; report ticks the contract line by line |
