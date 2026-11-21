# Harness facts: how to start, clean, cap, fence and resume a run

For the harness builder. Every item was checked on 2026-11-21 against Claude Code 2.1.302 on the
owner's Mac, signed in on the Max subscription (`claude auth status` shows `authMethod: claude.ai`,
`subscriptionType: max`). Each item gives the doc page and the trial that confirmed it. Trials ran in
`~/factory-runs/scout-scratch/` with Haiku 5.5 and one-line prompts.

Docs are cited by their Markdown copies, for example
<https://code.claude.com/docs/en/headless.md>. Drop the `.md` for the web page.

## The short version

One run, as the harness should start it:

```bash
cd "$SANDBOX" && DISABLE_AUTOUPDATER=1 CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
claude -p "$(cat brief.md)" \
  --model claude-opus-5-5 \
  --setting-sources project,local \
  --settings /abs/path/run-settings.json \
  --strict-mcp-config \
  --tools "Bash,Read,Edit,Write,Glob,Grep,Agent" \
  --max-budget-usd 12 \
  --output-format stream-json --verbose --include-hook-events \
  < /dev/null > run.jsonl 2> run.err
```

- Clean room: `--setting-sources project,local` plus `--strict-mcp-config`. Not `--bare`, which
  loses the subscription login and ignores hooks.
- Cap: `--max-budget-usd` works on the subscription. There is no token cap; convert the token ceiling
  to dollars at list price.
- Fence: the OS sandbox in the per-run settings file is the real wall. Deny rules and a PreToolUse
  hook are the second layer.
- Reply to a question: `claude -p "<reply>" --resume <session_id>` with the same flags. Totals
  carry over.
- Read the **last** `result` line, check `is_error`, not just `subtype`.
- Update the CLI to 2.1.321+ before stage 1 and freeze it; this Mac's 2.1.302 maps `fable` to
  Fable 5.1 (item 8). Use full model IDs.

## 1. Start a headless run with a fixed model, folder and full log

**How.** `claude -p "<prompt>" --model <alias-or-id> --output-format stream-json --verbose`, run from
the sandbox folder (the folder you start in is the working folder). Add `< /dev/null`, or the CLI
waits 3 seconds for stdin and prints a warning. Add `--include-hook-events` to log hook decisions too,
and `--forward-subagent-text` if you want subagents' own text and thinking, not only their tool calls.

**What the log holds.** One JSON object per line:

| Line `type` / `subtype` | What it is |
| --- | --- |
| `system` / `init` | First line. `session_id`, `model`, `cwd`, `permissionMode`, `tools`, `skills`, `agents`, `plugins`, `mcp_servers`, `claude_code_version`, `apiKeySource` |
| `assistant` | Each model message, with its `usage`. Tool calls are `tool_use` blocks inside it |
| `user` | Tool results (`tool_result` blocks), and a subagent's prompt |
| `system` / `hook_started`, `hook_response` | Hook runs, with exit code and stderr (needs `--include-hook-events`) |
| `system` / `api_retry` | A retry after an API error, with `error` category and delay |
| `rate_limit_event` | Plan-limit status (see item 7) |
| `result` | End of a turn: totals, cost, outcome |

Subagent messages carry `parent_tool_use_id` set to the Agent call that started them; main-thread
messages carry `null`.

**The result record** (trial t1, verbatim field names):

| Field | Example | Notes |
| --- | --- | --- |
| `subtype` | `success`, `error_max_turns`, `error_max_budget_usd`, `error_during_execution` | |
| `is_error` | `false` | **Check this.** A login failure came back as `subtype: success`, `is_error: true` |
| `terminal_reason` | `completed`, `max_turns`, `budget_exhausted`, `api_error`, `hook_stopped` … | Why the loop ended |
| `result` | `"OK"` | Final text. Absent on error subtypes; see `errors` instead |
| `session_id` | UUID | Needed to resume |
| `num_turns` | `1` | Turns in this call only |
| `total_cost_usd` | `0.0072` | Estimate at list price, includes subagents |
| `usage` | `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, plus `cache_creation.ephemeral_1h_input_tokens` / `ephemeral_5m_input_tokens` | **Main loop only**, excludes subagents |
| `modelUsage` | per model: `inputTokens`, `outputTokens`, `cacheCreationInputTokens`, `cacheReadInputTokens`, `costUSD`, `costBasis: "list"` | **Use this for token accounting.** Includes subagents and compaction |
| `subagent_stats` | `spawned`, `completed`, `failed`, `refused.budget` … | Free team-arm telemetry |
| `permission_denials` | list of `{tool_name, tool_input}` | Every blocked call; good drift evidence |
| `duration_ms`, `duration_api_ms` | | Wall time and API time |
| `result_index` | `0`, `1` … | Order of results in one process |

**Trap: more than one `result` per run.** In trial t8 the main agent launched a background subagent,
ended its turn (first `result`), then woke when the subagent finished and wrote a second `result`.
Always take the last `result` line (highest `result_index`).

Sources: <https://code.claude.com/docs/en/headless.md> (stream responses, follow subagent messages,
handle API retries), <https://code.claude.com/docs/en/agent-sdk/typescript.md> (`SDKResultMessage`),
<https://code.claude.com/docs/en/agent-sdk/cost-tracking.md>. Trials: t1
`claude -p "Reply with just OK" --model haiku --output-format stream-json --verbose`; t8 (subagent run, item 6).

**Where else the log lives.** Claude Code also saves its own transcript at
`~/.claude/projects/<folder-slug>/<session_id>.jsonl` (the hook input in t2 showed the path). The
stream file is enough for the harness; the transcript is what `--resume` reads, so don't pass
`--no-session-persistence` if you may need to reply.

**Agent SDK instead of the CLI?** Same engine and the same result fields (`query()` in TypeScript or
Python). It adds callbacks such as `canUseTool` and in-process hooks. The CLI is enough for this
harness and keeps one less dependency. Source: <https://code.claude.com/docs/en/agent-sdk/overview.md>.

## 2. Clean settings, still on the subscription

**Answer: `--setting-sources project,local` + `--settings <run file>` + `--strict-mcp-config`.**
Verified by trial t2.

| Option | Clean? | Keeps subscription login? | Per-run hooks work? | Verdict |
| --- | --- | --- | --- | --- |
| `--bare` | Yes: skips hooks, skills, plugins, MCP, memory, CLAUDE.md | **No.** Never reads OAuth or the keychain. Trial t3: `"Not logged in · Please run /login"` | **No.** Docs: hooks passed with `--settings` still don't run | Unusable here |
| `--setting-sources project,local` | Drops everything from `~/.claude` (user skills, user hooks, user settings such as `defaultMode: auto`, user plugins) | Yes | Yes, via `--settings` | **Use this** |
| `--settings <file>` | Adds, doesn't remove: most lists merge with the user's files | Yes | Yes | Use **with** the line above, for the run's own rules and hooks |
| `CLAUDE_CONFIG_DIR=<fresh dir>` | Fully clean | **No.** The keychain entry is keyed to the folder. Trial t3: `loggedIn: false` | Yes | Only with a `claude setup-token` token in `CLAUDE_CODE_OAUTH_TOKEN`, which needs the owner's browser approval |

What the clean run still had (t2 `system/init`), and how to drop each:

- **Built-in skills** such as `code-review`, `simplify`, `deep-research`. These ship with Claude Code;
  they are not the owner's. To remove them too, add `--disable-slash-commands` (all skills and
  commands off) or leave `Skill` out of `--tools`.
- **Built-in plugins** (`cc-plugin-agents-md`, `cc-plugin-telemetry`, `cc-plugin-plugin-authoring`).
  These are part of the app.
- **Extra tools** (`Artifact`, `CronCreate`, `WebSearch`, `Workflow`, `SendMessage` …). Remove them
  with `--tools "Bash,Read,Edit,Write,Glob,Grep"` (add `Agent` for the team arm).
- **The claude.ai connectors** (Google Drive, Notion, Calendar, Claude Docs) load from the account,
  not from settings. `--strict-mcp-config` removed them (`mcp_servers: []`).
- **Auto memory**: add `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` to the run's environment.

The proof (t2, run with the flags above):

- User skills `file-issue`, `triage`, `work-ticket` were in the normal run's `skills` list (t1) and
  absent from the clean run.
- The owner's PreToolUse guard hook did not fire; only the run's own hook did (one `hook_started`
  event, `PreToolUse:Bash`, from the per-run settings).
- `permissionMode` was `dontAsk` from the run file, not the owner's `auto`.
- `apiKeySource: none` and a normal cost: the subscription login was used.

**Leave the guard hook question to the owner:** the clean run also drops the owner's
`guard-main-checkout.py` hook. Runs work in `gct-lab`, not the real checkout, so this is fine, but the
harness can copy that hook into the run settings to keep the extra safety.

Sources: <https://code.claude.com/docs/en/headless.md#start-faster-with-bare-mode>,
<https://code.claude.com/docs/en/cli-reference.md>, <https://code.claude.com/docs/en/authentication.md>
(credential management, `setup-token`, precedence), <https://code.claude.com/docs/en/agent-sdk/claude-code-features.md>
(what `settingSources` does not control). Trials: t2, t3
(`claude --bare -p …`, `CLAUDE_CONFIG_DIR=<empty dir> claude -p …`).

## 3. Capping a run

**Answer: `--max-budget-usd` and `--max-turns` both stop a subscription run. There is no token cap.**

Trial t4 (Haiku, prompt asking for three separate `echo` calls):

| Flag | Result | Exit code |
| --- | --- | --- |
| `--max-budget-usd 0.001` | `subtype: error_max_budget_usd`, `terminal_reason: budget_exhausted`, `errors: ["Reached maximum budget ($0.001)"]`, stopped after 1 turn at $0.0019 | 1 |
| `--max-turns 2` | `subtype: error_max_turns`, `terminal_reason: max_turns`, `errors: ["Reached maximum number of turns (2)"]` | 1 |

Points that matter:

- **The dollar figure is an estimate at list price** (`costBasis: "list"`), not a bill. On the Max plan
  nothing is charged per run; the cap still works because it checks the estimate. So it is a fine
  stand-in for a token ceiling: take the stage's token ceiling, price it at the model's list rates,
  and pass that.
- **It overshoots by up to one step.** It checks after each model call, so the run in t4 ended at
  $0.0019 against a $0.001 cap. Docs say leave headroom.
- **Subagent spend counts toward it.** At the cap, new subagents are refused and background ones are
  stopped.
- **On `--resume`, only the new call's spend counts against the cap.** Earlier spend restored from
  the session does not. The harness must pass the remaining budget, not the original.
- **No token-count cap exists** in the CLI or SDK. `CLAUDE_CODE_MAX_OUTPUT_TOKENS` limits one reply,
  not the run. If an exact token ceiling is required, the harness has to watch `usage` on each
  `assistant` line (count each message `id` once) and stop the process.
- **Stopping from outside:** SIGINT ends the turn cleanly; SIGTERM exits with code 143 and writes no
  `result` for the unfinished turn, so count tokens from the lines already logged.
- Subagent fan-out limits: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (default 3) and
  `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20), set as environment variables.

Sources: <https://code.claude.com/docs/en/cli-reference.md> (`--max-budget-usd`, `--max-turns`),
<https://code.claude.com/docs/en/agent-sdk/cost-tracking.md> (estimates, not billing),
<https://code.claude.com/docs/en/agent-sdk/subagents.md> (cap depth, concurrency and spend),
<https://code.claude.com/docs/en/headless.md#stop-a-run-with-sigterm>. Trial: t4.

## 4. Restricting a run

**Answer: put the OS sandbox in the per-run settings file. It is the only layer that does not
depend on how a command is spelled. Use deny rules and a PreToolUse hook as a second layer.**

The per-run settings file that passed every check in trials t5 and t6 (paths shortened):

```json
{
  "permissions": {
    "defaultMode": "dontAsk",
    "allow": ["Bash", "Read", "Edit(./**)", "Bash(/abs/harness/bin/gh-wrap.sh *)"],
    "deny": ["WebFetch", "WebSearch", "Bash(gh *)", "Bash(git push *)", "Bash(git fetch *)",
             "Bash(git pull *)", "Bash(git clone *)", "Edit(//abs/harness/**)"]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "allowUnsandboxedCommands": false,
    "failIfUnavailable": true,
    "excludedCommands": ["/abs/harness/bin/gh-wrap.sh *"],
    "network": { "allowedDomains": [] }
  }
}
```

What each piece did in trial t5/t6:

| Attempt by the run | Stopped by | Seen in the log |
| --- | --- | --- |
| `curl https://example.com` | Sandbox network | `deny network-outbound example.com:443` |
| `echo x > ../outside.txt` | Sandbox filesystem | `operation not permitted` |
| `gh --version` | Deny rule | `Permission to use Bash with command gh --version has been denied` |
| `git push origin main` | Deny rule (and the sandbox would block the network anyway) | same message |
| WebFetch | Tool not offered | `No matching deferred tools found` |
| Write tool to a file outside the folder | `dontAsk` + `Edit(./**)` only | listed in `permission_denials` |
| Write tool into the wrapper's folder | `Edit(//abs/…/**)` deny rule | listed in `permission_denials` |
| `/abs/…/gh-wrap.sh hello` | **Allowed**, ran outside the sandbox with network | `wrapper ran, network http=200` |

Traps found on the way:

- **Absolute paths need two slashes.** `Edit(/Users/x/bin/**)` is read as relative to the settings
  file's folder. In t5 the Write tool wrote into the "protected" folder until the rule was changed to
  `Edit(//Users/x/bin/**)`.
- **`Write(path)` rules match nothing.** Use `Edit(path)`; it covers Write and NotebookEdit.
- **`permissions.blockWritesOutsideWorkingDirectories` needs v2.1.314.** This Mac has 2.1.302, so
  don't rely on it yet. Allowing only `Edit(./**)` under `dontAsk` does the same job today.
- **The wrapper script must live outside the sandbox folder, and be write-denied.** Anything in
  `excludedCommands` runs with full access; if the run could edit the wrapper it could run anything.
- **Deny rules match command text, not programs.** Docs: `Bash(git push *)` does not stop
  `git -C . push` or `sh -c 'git push'`. That is why the sandbox, which blocks the network for every
  spelling, is the main wall.
- **`dontAsk` is the right mode for unattended runs.** Anything not allowed is refused, never
  prompted. It also refuses the sandbox's "retry outside the sandbox" escape. `bypassPermissions` and
  `auto` are looser.
- The sandbox wraps Bash only. Read, Edit, Write and web tools follow the permission rules; hooks and
  MCP servers run unsandboxed.

**Is a PreToolUse hook more reliable?** It is more flexible, not stronger. A hook that exits with
code 2 blocks the call before any allow rule, and it can apply logic a rule can't (resolve real
paths, block by which agent is calling). In trial t6 a 9-line hook (`guard-writes.sh`: resolve the
path, refuse if outside `cwd`) blocked both outside writes just as the rules did. But a hook that reads
Bash command text can be dodged by the same tricks as a rule. Order of strength: sandbox, then
hook, then rule. Hooks passed in `--settings` do run (t2, t6); hooks are skipped only under `--bare`.

Sources: <https://code.claude.com/docs/en/permissions.md> (Bash rule limits, path patterns, hooks
precedence, working directories), <https://code.claude.com/docs/en/sandboxing.md> (what it restricts,
strict mode, `excludedCommands`), <https://code.claude.com/docs/en/permission-modes.md>,
<https://code.claude.com/docs/en/hooks.md>. Trials: t5, t6 (`rules.json` versus `hook.json`).

## 5. Replying to a run that stopped on a question

**Answer: `claude -p "<reply>" --resume <session_id>` with the same flags, from the same folder. It
continues the same session, and cost and per-model tokens accumulate.**

Trial t7: run 1 asked "What's your favourite colour?" and ended. Run 2 resumed with "Blue…" and
answered "BLUE".

| Call | `session_id` | `num_turns` | `total_cost_usd` | `usage` output tokens | `modelUsage` output tokens |
| --- | --- | --- | --- | --- | --- |
| First run | 58a6f1af… | 1 | 0.00138 | 11 | 11 |
| Resume | 58a6f1af… (same) | 1 | 0.00267 | 6 | 17 |

So:

- `total_cost_usd` and `modelUsage` on the resumed result are **session totals**. Read the latest
  result; summing results double-counts.
- `usage` and `num_turns` cover **only that call**.
- `--max-budget-usd` on the resume counts only the new call's spend (item 3).
- Settings, tools and agents are not stored in the session. Pass the same `--settings`,
  `--setting-sources`, `--tools`, `--agents` again, or the reply runs with different rules.
- `--fork-session` makes a new session ID instead, if a branch is wanted.

Sources: <https://code.claude.com/docs/en/cli-reference.md> (`--resume`),
<https://code.claude.com/docs/en/agent-sdk/cost-tracking.md#accumulate-costs-across-multiple-calls>.
Trial: t7.

## 6. Per-run subagents for the team arm

**Answer: `--agents <file.json>` defines agents for one run only. Each can have its own `model`,
`tools`, `prompt`, `permissionMode`, `maxTurns`, `effort`, `hooks` and `isolation`. One role can be
kept from seeing another's files with a hook inside that role's definition.**

Trial t8 file (`agents.json`):

```json
{
  "tester": {
    "description": "Writes tests from the contract only. Use for any testing task.",
    "prompt": "You are the tester. Read only the contract. ...",
    "model": "haiku",
    "tools": ["Read", "Glob", "Grep"],
    "hooks": { "PreToolUse": [ { "matcher": "Read|Glob|Grep",
      "hooks": [ { "type": "command", "command": "/abs/hide-src.sh" } ] } ] }
  }
}
```

Result: `tester` appeared in `system/init` `agents`. It read `contract.md`, and its read of
`src/impl.txt` was refused: `PreToolUse:Read hook error: … Blocked: the tester may not look at the
builder's code in src/`. Its messages were tagged with the Agent call's ID in `parent_tool_use_id`.

For the five P4 roles:

- Define planner, architect, builder, tester and reviewer in one JSON file, each with its own model
  (for example Fable for planner and reviewer, Opus for builder) and tool list. The file form of
  `--agents` needs v2.1.281+, which this Mac has.
- **Keeping the tester blind:** give it a role-scoped hook (as above). If the tester needs Bash to run
  tests, its hook must also refuse Bash commands that mention the code folder, or better, have it
  write tests only and let the lead run them. A session-wide hook can do the same: hook input carries
  `agent_type`, so one script can apply per-role rules.
- `isolation: "worktree"` gives a role its own git worktree, branched from the default branch, not
  from the builder's uncommitted work. That is another way to keep a role from seeing in-progress
  code.
- `omitClaudeMd: true` keeps project memory out of a role's context.
- Hooks in `--agents` definitions run without the folder trust step that `-p` lacks; hooks in a
  project's `.claude/agents/*.md` files do not run under `-p`.
- Token accounting: `modelUsage` splits by model, and `subagent_stats` counts spawns and failures.
  Each role's own share needs grouping the stream by `parent_tool_use_id`.

Sources: <https://code.claude.com/docs/en/sub-agents.md> (choose the subagent scope, frontmatter
reference, hooks in subagent frontmatter), <https://code.claude.com/docs/en/hooks.md> (`agent_type`).
Trial: t8.

## 7. Telling a plan-limit stop from a real failure

**Not triggered on purpose** (it would burn the owner's plan). From the docs plus the event seen in
every trial:

- Every run writes a `rate_limit_event` line. In t1 it read
  `{"status": "allowed", "rateLimitType": "seven_day", "resetsAt": 1795345200, …}`. `status` is
  `allowed`, `allowed_warning` or `rejected`. A `rejected` event means the plan limit was hit;
  `resetsAt` is the Unix time to retry after.
- The run then ends with `is_error: true`, and the text is one of: `You've hit your session limit ·
  resets 3:45pm`, `You've hit your weekly limit · …`, `You've hit your Opus limit · …`. Session and
  weekly limits cover all models; the Opus limit can be dodged by switching model family.
- **Short throttles are retried for you.** `API Error: Server is temporarily limiting requests (not
  your usage limit)` and `529 Overloaded` are retried with backoff first, each try logged as a
  `system/api_retry` line with `error: "rate_limit"` or `"overloaded"`. Only if retries run out does
  the run fail.

A classifier the harness can use:

| Seen | Meaning | Harness action |
| --- | --- | --- |
| `rate_limit_event.status == "rejected"`, or result text starts `You've hit your` | Plan limit | Sleep until `resetsAt`, then rerun or resume. Don't count as a run failure |
| Result `is_error`, `api_error_status` 429 or 529, or text has `Overloaded` / `temporarily limiting` | Capacity | Retry after a few minutes |
| `Not logged in · Please run /login` | Login lost | Stop the stage, tell the owner |
| `error_max_budget_usd` / `error_max_turns` | Our cap | Score as capped |
| Exit 143, no result | Killed by SIGTERM | Count tokens from the log so far |
| Anything else with `is_error: true` | Real failure | Score it |

One caution: the Desktop app and interactive CLI can auto-continue after a limit resets; a `-p` run
just ends, so the harness owns the retry.

Sources: <https://code.claude.com/docs/en/errors.md> (usage limits, server is temporarily limiting
requests, 429, 529), <https://code.claude.com/docs/en/agent-sdk/typescript.md> (`SDKRateLimitEvent`,
`terminal_reason`), <https://code.claude.com/docs/en/headless.md#handle-api-retries>. Observed:
`rate_limit_event` in t1.

## 8. Version and model names (found later, while writing the scout report)

**Update the CLI once before stage 1, then freeze it.** The docs describe a newer Claude Code than
this Mac's 2.1.302, and the model names depend on the version.

- **`--model fable` ran Fable 5.1, not 5.2** (trial t9: `system/init` `model: claude-fable-5-1`).
  Docs: Fable 5.2 needs v2.1.321 or later; on older versions the alias falls back.
- **`--model claude-fable-5-2` does reach Fable 5.2 on 2.1.302** (trial t10: `modelUsage` key
  `claude-fable-5-2`), but stderr prints `[claude-code:unrecognized_model]`, and the CLI's price table
  doesn't know the model, so `total_cost_usd` and `--max-budget-usd` can be wrong for it.
- Opus 5.5 needs v2.1.280+ (fine); `blockWritesOutsideWorkingDirectories` needs v2.1.314 (not
  available yet).
- **Fix:** `claude update`, check `claude --version` is at least 2.1.321, then set
  `DISABLE_AUTOUPDATER=1` in every run's environment so the version can't change mid-stage. Record
  `claude_code_version` from each run's `system/init` line. Pass full model IDs
  (`claude-opus-5-5`, `claude-fable-5-2`), not aliases, so a later release can't move them.
- **Fable billing.** On this account Fable drew on the plan, not on usage credits (t9
  `rate_limit_event`: `isUsingOverage: false`, `overageStatus: rejected`,
  `overageDisabledReason: org_level_disabled`). Docs warn that in `-p` mode a Fable request that would
  bill to usage credits is billed **without asking**. Usage credits are off at the moment, so this
  can't cost money today; if the owner ever turns them on, cap Fable runs by budget first.
- A two-word Fable 5.1 reply cost $0.086 at list price, mostly writing the ~30k-token system prompt to
  the cache. A run's fixed start-up cost is far higher on Fable than on Haiku; trimming tools with
  `--tools` shrinks it.

Sources: <https://code.claude.com/docs/en/model-config.md> (model aliases, work with Fable, Fable and
usage credits), <https://code.claude.com/docs/en/errors.md> (unrecognized model ID on a request),
<https://code.claude.com/docs/en/env-vars.md> (`DISABLE_AUTOUPDATER`). Trials: t9
`claude -p "Reply with just OK" --model fable --tools "" …`, t10 same with `--model claude-fable-5-2`.

## Trial log

All on 2026-11-21, Haiku 5.5 unless noted (t9, t10 used Fable), in `~/factory-runs/scout-scratch/`. Totals across the trials
above plus the Part 2 trials: about 180k new tokens (input, output and cache writes; most of it is
the ~30k-token system prompt written to the cache once per run) plus about 0.8M cheap cache reads,
about $0.25 at list price.

| Trial | What | Outcome |
| --- | --- | --- |
| t1 | Plain `-p` run, stream-json | Full result record; user skills, hooks, connectors all loaded |
| t2 | `--setting-sources project,local --settings … --strict-mcp-config` | Clean, still signed in, per-run hook ran |
| t3 | `--bare`; fresh `CLAUDE_CONFIG_DIR` | Both "Not logged in" |
| t4 | `--max-budget-usd 0.001`; `--max-turns 2` | Both stopped the run, exit 1 |
| t5 | Sandbox + deny rules + wrapper | Network and outside writes blocked, wrapper allowed; found the `//` path trap |
| t6 | Write limits by rules versus by hook | Both blocked outside writes |
| t7 | Ask, then `--resume` with a reply | Same session, totals accumulate |
| t8 | Tester subagent from `--agents`, with `src/` hidden by a role hook | Contract read, `src/` refused; two `result` lines in one run |
| t9 | `--model fable`, tools off | Ran Fable 5.1; drew on the plan, not usage credits |
| t10 | `--model claude-fable-5-2` | Worked, with an unrecognized-model warning |
