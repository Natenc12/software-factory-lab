# Arm sizes

Words a run of each arm receives from its folder, counted as whitespace-separated words (`wc -w`).
Up front: the instruction files appended to the system prompt, the agent definitions passed with
`--agents` (front matter included), and each skill's description. On demand: each skill's body, which
loads only when the run calls the skill. The shared run prompt (`harness/prompts/run.md`) and the ticket come on top,
the same for every arm. `tests/test_arms.py` checks every column against the files. No stage 1 arm has skills; P5, P5P and P5PA are the only arms with them.

| Arm | Name | Up front | Instructions | Agents | Skill descriptions | Skill bodies (on demand) |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | Bare | 0 | none | none | none | none |
| P1 | Loose | 145 | `GUIDE.md` 145 | none | none | none |
| P1R | Loose + reviewer | 594 | `GUIDE.md` 221 | `reviewer` 373 | none | none |
| P3 | Contract | 2,104 | `SKILL.md` 1,655 | `reviewer` 449 | none | none |
| P2 | Checklist | 1,713 | `SKILL.md` 1,332 | `reviewer` 381 | none | none |
| P4 | Team | 1,975 | `LEAD.md` 727 | `planner` 299, `architect` 176, `builder` 198, `tester` 251, `reviewer` 324 | none | none |
| P1T | Tests first | 190 | `GUIDE.md` 190 (P1 + 45) | none | none | none |
| P1L | Small slices | 179 | `GUIDE.md` 179 (P1 + 34) | none | none | none |
| P1A | Architecture brief | 776 | `GUIDE.md` 167 (P1 + 22), `SYSTEM-MAP.md` 609 | none | none | none |
| P5 | Skills library | 268 | `GUIDE.md` 148 (P1 + 3) | none | 120 | 408 |
| P5P | Skills library, pointed | 288 | `GUIDE.md` 168 (P5 + 20) | none | 120 | 408 |
| P5PA | Pointed skills + architecture brief | 919 | `GUIDE.md` 190 (P5P + 22), `SYSTEM-MAP.md` 609 | none | 120 | 408 |

For comparison, the sources: race 1 shape B 1,840 + reviewer brief 385; the owner's `work-ticket`
skill 1,621 + reviewer brief 330 + templates README 229. P4's role limits also ship a hook script
(`hooks/role_guard.py`) that the run never reads as instructions.

P1 is 145 words against an aim of under 250. Not every word reaches the model in the same place: the
agent definitions' prompts go to the subagents, and only their descriptions sit in the lead's context.

P5, P5P and P5PA skills (the same files), description (up front) and body (on demand) in words: check-the-ask 34 and 90,
prove-each-claim 22 and 90, test-that-bites 9 and 70, find-the-cause 17 and 51, stay-in-scope 26 and
41, fresh-eyes-review 12 and 66. Each skill's `name:` line is not counted.
