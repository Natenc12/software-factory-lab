# Arms

One folder per arm for stage 1, in tie order: `P0` Bare, `P1` Loose, `P1R` Loose + reviewer, `P3`
Contract, `P2` Checklist, `P4` Team. A run gets an arm with `--arm arms/<name>`; a bare run gets no
`--arm`.

What a run receives from a folder: its top-level `.md` files other than `README.md`, appended to the
system prompt, and `agents/*.md`, passed as `--agents` (see `harness/README.md`). Nothing else here
is loaded into a run:

- `CHANGES.md`: every departure from the arms' sources, with the reason.
- `SIZES.md`: each arm's word count.
- `P4/hooks/`: the team's per-role hooks, run by Claude Code, never read as instructions.
