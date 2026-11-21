# Arm sizes

Words a run of each arm receives from its folder, counted as whitespace-separated words (`wc -w`):
the instruction files appended to the system prompt plus the agent definitions passed with `--agents`
(front matter included). The shared run prompt (`harness/prompts/run.md`) and the ticket come on top,
the same for every arm. `tests/test_arms.py` checks the totals against the files.

| Arm | Name | Total words | Instructions | Agents |
| --- | --- | --- | --- | --- |
| P0 | Bare | 0 | none | none |
| P1 | Loose | 145 | `GUIDE.md` 145 | none |
| P1R | Loose + reviewer | 594 | `GUIDE.md` 221 | `reviewer` 373 |
| P3 | Contract | 2,104 | `SKILL.md` 1,655 | `reviewer` 449 |
| P2 | Checklist | 1,713 | `SKILL.md` 1,332 | `reviewer` 381 |
| P4 | Team | 1,975 | `LEAD.md` 727 | `planner` 299, `architect` 176, `builder` 198, `tester` 251, `reviewer` 324 |

For comparison, the sources: race 1 shape B 1,840 + reviewer brief 385; the owner's `work-ticket`
skill 1,621 + reviewer brief 330 + templates README 229. P4's role limits also ship a hook script
(`hooks/role_guard.py`) that the run never reads as instructions.

P1 is 145 words against an aim of under 250. Not every word reaches the model in the same place: the
agent definitions' prompts go to the subagents, and only their descriptions sit in the lead's context.
