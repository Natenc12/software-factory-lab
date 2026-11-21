# Recorded trials

Real `claude -p` calls made while building the harness, on 2026-11-21, Claude Code 2.1.302, signed in
on the Max subscription, model `claude-haiku-5-5`. Four calls in all, about 25k counted tokens, about
$0.01 at list price. Paths are shortened.

## Trial 1: clean-room flags, guard hook, record formats

A bare folder, `env -i` with only `HOME`, `PATH`, `USER`, `LANG`, and:

```
claude -p "Run 'gh --version'. Then list every skill you can use, and quote any CLAUDE.md or memory text."
  --output-format stream-json --verbose --include-hook-events --model claude-haiku-5-5
  --setting-sources "" --settings <trial settings with one PreToolUse hook>
  --disable-slash-commands --strict-mcp-config --permission-mode dontAsk
  --disallowedTools WebFetch WebSearch --no-chrome
```

| Check | Seen |
| --- | --- |
| User skills (`work-ticket`, `triage`, `file-issue` live in `~/.claude/skills`) | `system/init` `skills: []`, `slash_commands: []` |
| User hooks (the owner's settings have a PreToolUse guard) | one `hook_started` only, from the trial's own settings |
| User output style (set in user settings) | `output_style: default` |
| MCP servers and connectors | `mcp_servers: []` |
| Memory | the model answered "CLAUDE.md/memory: NO" |
| Login | ran on the subscription |
| The trial's hook | denied `gh --version`; the tool result read `PreToolUse:Bash hook error: gh is blocked in this lab` |
| Records | `assistant` records repeat one `message.id` with the same `usage`; `result` has `usage`, `modelUsage`, `total_cost_usd`, `num_turns`, `is_error`, `subtype`, `permission_denials`; a `rate_limit_event` with `status: allowed` and `resetsAt` |

The default tool list also held `SendMessage`, `RemoteTrigger`, `CronCreate`, `PushNotification` and
other app tools, so the harness passes `--tools` with an explicit list.

## Trial 2: the harness itself, one run with a stop

`python -m harness.run zz-t0-1 --stage trial --arm <arm with ARM.md and agents/probe.md> ...` on a local
throwaway git repo (no GitHub, `--db none`, reply judge `claude-haiku-5-5`). The "ticket" told the run to
try `gh --version`, `cat ~/.claude/settings.json`, start the `probe` subagent (which tries `git fetch`),
write a page, and stop with `STOP: Should I continue? page: ../scratch/q.md`. Three calls: session, judge,
resume.

| Check | Seen |
| --- | --- |
| Tools offered | `Task, Bash, Edit, Glob, Grep, NotebookEdit, Read, Write` (the name `Agent` in `--tools` was ignored without error) |
| Arm subagents | `probe` listed in `system/init` `agents` |
| Guard, main session | `gh --version` and the read of `~/.claude/settings.json` denied |
| Guard, inside the subagent | `git fetch` denied: hooks from `--settings` also cover subagents |
| Stop and reply | judge answered `default`; the page was saved and stripped; owner-log entry written |
| Resume | same `session_id`; the run received the reply text word for word and echoed it |
| Two results in one call | the subagent ran in the background, so the first call wrote two `result` records (`result_index` 0 and 1); the harness reads the last and sums `num_turns` over all |
| Token totals | `modelUsage` in each result is a running total for the session; the harness takes the difference per call. Run total: input 20, output 2,845, cache write 18,044, cache read 78,776, counted 20,909 |
| Leak scan | `python -m harness.scan` on the transcript: clean, 7 tool calls, 3 blocked attempts |

The Claude Code scout's notes (`research/harness-facts.md` on its branch) agree: `--setting-sources`
without `user` is the clean room that keeps the subscription login (`--bare` and a fresh
`CLAUDE_CONFIG_DIR` both lose it), and resumed results carry session totals.
