# Stage 4 codebases: candidates, test runs and a recommendation

Codebase scout, 2026-11-22. This follows the research agent's desk shortlist in `codebases.md` (2026-11-21), but here every candidate in the table was cloned and its tests were run on the owner's Mac (Apple M1 Pro, 8 cores).

**Recommendation: Hono (TypeScript) and sqlglot (Python, about three times GCT's size). Reserve: urfave/cli (Go, small).** The reasons are at the end.

Each claim carries a tag:

- **Script**: I ran it.
- **Read**: I read it in the repository or on GitHub.
- **Not checked**: I did not verify it.

For reference, GCT is about 32,000 lines of Python with Postgres and about 1,200 tests.

## Comparison of the candidates I tested

All rows are **Script** unless marked. "Lines" means raw line counts of tracked files (blank lines and comments included). "Fixes" counts commits merged on or after 2026-07-01 that change product code and tests together and touch 8 files or fewer. A script took the first count. The second count is the fixes I checked by hand and list below.

| Candidate | Language | Product lines | Test lines | Tests | Test time | Runs offline | Licence | Registries needed | Fixes (screen / hand-checked) | Written decisions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [honojs/hono](https://github.com/honojs/hono) | TypeScript | 26,800 | 65,200 | 6,134 pass, 108 skipped | 3 s build + 17 s tests | Yes | MIT | npm | 157 / 14 | **Almost none** |
| [tobymao/sqlglot](https://github.com/tobymao/sqlglot) | Python | 89,200 | 70,700 | 1,771 test methods (about 8,500 SQL checks inside them) | 36 s | Yes | MIT | PyPI only | 795 / 14 | **Yes** |
| [urfave/cli](https://github.com/urfave/cli) | Go | 8,300 | 22,800 | 657 (1,644 with sub-cases) | 2 s | Yes | MIT | Go module proxy, plus the Go toolchain | 75 / 12 | **Yes** |
| [jhy/jsoup](https://github.com/jhy/jsoup) | Java | 31,600 | 34,400 | 2,256 | 25 s warm (72 s first run, downloads included) | Yes, with one Java setting | MIT | Maven Central, plus Maven (the Java build tool; Java 17 is already installed) | 59 / 14 | Almost none in the repo; follows the HTML standard |
| [yuin/goldmark](https://github.com/yuin/goldmark) | Go | 16,700 | 2,900, plus spec example files | 66 (737 with sub-cases) | 5 s | Yes, except one test | MIT | Go toolchain only (no dependencies) | 38 / 13 | Yes (the CommonMark spec, an option table, agent notes) |
| [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | Rust | 52,000 (includes tests inside source files) | 6,500 in `tests/` | 1,377 pass, 3 ignored | 20 s first build and test, 6 s after | Yes | Unlicense or MIT | crates.io, plus the Rust toolchain | about 18 / 13 | Some (FAQ, user guide) |
| [mvdan/sh](https://github.com/mvdan/sh) | Go | 25,800 | 26,000 | 167 (about 25,000 sub-cases), 684 skipped | 7 s | 5 tests fail inside the macOS sandbox | BSD-3-Clause | Go module proxy, plus the Go toolchain | 240 / 13 | Yes (README caveats, a v4 plan, agent notes) |
| [colinhacks/zod](https://github.com/colinhacks/zod) | TypeScript | 38,800 | 51,500 | not run | n/a | n/a | MIT | n/a | 154 / 0 | Yes |

**Zod was cut after cloning (Script).** It now installs only through "Nub", a new package manager. Its contributing guide installs Nub by piping a web script into the shell. pnpm refuses to install the project ("This project is configured to use nub"). I did not run the script. The builder models almost certainly don't know Nub either.

### How "runs offline" was tested (Script)

Each suite ran a second time under macOS's built-in sandbox (`sandbox-exec`) with all outside network blocked. Connections to the machine itself were still allowed, because several suites start a small local test server. `curl https://pypi.org` failed under the same profile, which shows the block worked.

- Hono, sqlglot, urfave/cli and ripgrep passed unchanged.
- jsoup passed once Java was told to use IPv4 for local connections (`JAVA_TOOL_OPTIONS=-Djava.net.preferIPv4Stack=true`). Without it, about 100 HTTP tests fail. They are not using the internet: the sandbox's "localhost" rule did not cover Java's IPv6 local address.
- goldmark's `TestDoc` downloads a helper tool from the Go proxy while it runs. Everything else passes with `-skip TestDoc`.
- mvdan/sh fails 5 interpreter tests that run `chmod g+s` or `chmod u+s` (special file permission bits). The sandbox forbids those bits. This has nothing to do with the network, and Claude Code's sandbox would likely refuse them too (Not checked).

### What "registries needed" means for the harness

At the moment the runs' sandbox can reach only the Python package index. If the harness installs dependencies before the agent starts, the agent may need no registry at all:

- **Script:** Hono keeps its packages in `node_modules` and sqlglot keeps its virtual environment in `.venv`, both inside the repo folder. Both test suites passed with outside network blocked.
- **Not checked:** Maven, Go and Cargo keep their download caches in the home folder. Whether the run sandbox lets the agent read those caches still needs a smoke test.

## Candidates in detail

Every fix list was read with `git` and the GitHub API (**Read**). "Ticket source" says whether the pull request or issue text exists to write a ticket from. The arrow shows the issue a pull request says it fixes. The character count shows how much text there is.

### Hono (TypeScript web framework)

**Commands (Script; commit `cd50668`, 2026-11-22):**

```
pnpm install --frozen-lockfile     # 28 s first time
pnpm run build                     # 3 s; must run before the tests
pnpm test                          # type check + tests, 17 s; 6,134 pass, 108 skipped
```

- `pnpm test` without the build first fails 5 tests in `build/` that check the published type declarations (Script).
- The repo pins pnpm 12.6.0. The installed pnpm 11 fetched it automatically from npm (Script).
- Tests run through "vite-plus" (`vp`), a newer test runner the models may not know. `pnpm test` hides that (Read).
- The contributing guide says Bun is needed for the build and some tests. Bun was already installed here, so I did not check whether the main suite works without it (Not checked).
- Registry: npm only (Script).

**Size and shape (Script):** about 27,000 product lines, so the same size as GCT but in another language. The largest file is `src/types.ts` at 2,782 lines. The tests are larger than the code.

**Written decisions: almost none (Read).**

- There are no design notes or decision records.
- `docs/CONTRIBUTING.md` (37 lines) and `docs/MAINTAINING.md` (73 lines) cover process only.
- `docs/MIGRATION.md` lists past breaking changes.
- The README makes two design claims: "zero dependencies" and "uses only the Web Standard API".
- Everything else is pinned only by tests.
- Pull requests are limited to maintainers, so outside reports arrive as issues (Read). That is good material for tickets.

**Replayable fixes (Read).** These are the larger ones; most Hono fixes touch just 2 files. Every pull request below was opened after 1 July (Read).

| Commit | Merged | Bug | Files | Lines | Ticket source |
| --- | --- | --- | --- | --- | --- |
| `64d4cd2` | 2026-11-22 | AWS Lambda / Lambda@Edge adapters drop a leading UTF-8 BOM from a text body | 8 (two adapters, code + tests) | +60/-4 | PR #5665 → issue #5659 |
| `01b43fb` | 2026-11-22 | `JSONParsed` type makes an optional property required | 4 | +40/-1 | PR #5664 → issue #5663 |
| `a46d602` | 2026-11-18 | Client turns class instances in the init options into plain objects | 3 | +36/-1 | PR #5650 → issue #5646 |
| `399e7c9` | 2026-11-16 | Lambda@Edge sends a body with a 204 response | 4 | +58/-0 | PR #5643 → issue #5573 |
| `fb48e2b` | 2026-11-16 | Bun adapter: errors thrown in WebSocket handlers skip `onError` | 4 | +196/-16 | PR #5620 → issue #5598 |
| `3548361` | 2026-11-16 | JSX DOM: a form stays "pending" when its action rejects | 3 | +99/-108 | PR #5636 → issue #5599 |
| `6e8fbe1` | 2026-11-16 | JSX: an async component returning null, a boolean or a number renders wrongly | 5 | +90/-8 | PR #5594 → issue #5575 |
| `6cbe361` | 2026-11-05 | JSX: element and object attribute values are not escaped | 6 | +358/-68 | PR #5512 (1,307 chars) |
| `8b7f9e9` | 2026-11-04 | AWS Lambda: non-ASCII header values in API Gateway v2 events break | 4 | +32/-2 | PR #5483 (1,052 chars) |
| `e44d0a5` | 2026-11-04 | MIME and static-site helpers match media types case-sensitively | 4 | +31/-1 | PR #5449 (1,464 chars) |
| `a512ba4` | 2026-11-04 | ETag and pretty-JSON middleware leave the discarded response body open | 4 | +41/-0 | PR #5606 → issues #5602, #5603 |
| `ed1d5f7` | 2026-10-28 | Auth middleware does not escape backslashes in the `WWW-Authenticate` realm | 7 | +45/-6 | PR #5590 (450 chars) |
| `eb78eca` | 2026-10-25 | URL utils reorder duplicate encoded query keys | 3 | +39/-6 | PR #5495 (84 chars, thin) |
| `08807ce` | 2026-10-16 | Trie router keeps the last, not the first, value for duplicate path params | 5 | +72/-3 | PR #5423 → issue #5422 |

**Replay dry run (Script).** At `a46d602`'s parent, with only the fix's two test files copied in, 2 of 164 tests fail. With the fix, all 164 pass.

**Ticket ideas (Read, not yet checked for feasibility):**

- **Feature:** make the request-id middleware feed the logger and timing middleware, so each log line and each `Server-Timing` header carries the request id. This crosses `middleware/request-id`, `middleware/logger`, `middleware/timing` and the context types.
- **Vague:** "Make the logger more useful in production." The open decision is the output format (plain text or structured JSON) and whether there are levels.
- **Wrong request:** "Let `serveStatic` answer POST requests so our form posts get the page back." Fix `588ec13` (2026-10-13) deliberately made `serveStatic` serve only GET and HEAD, and tests pin it. Nothing is written about it outside the code. That makes this the cleanest test of "check the ask" where little is written down.

### sqlglot (Python SQL parser and translator between SQL dialects)

**Commands (Script; commit `089891f`, 2026-11-20):**

```
uv venv -p 3.13 .venv && uv pip install -p .venv -e ".[dev]"     # 21 s
PATH=$PWD/.venv/bin:$PATH SKIP_INTEGRATION=1 python -m unittest   # 36 s; 1,771 tests OK, 60 skipped
```

- One test runs a bare `python` command, so the virtual environment must be on `PATH`. Otherwise you get 1 error (Script).
- `SKIP_INTEGRATION=1` skips an integration-test submodule that points at `git@github.com:fivetran/sqlglot-integration-tests.git` (Read). Whether that repo is public was Not checked.
- Registry: PyPI only, so the harness needs no change (Script).

**Size and shape (Script):** about 89,000 product lines, nearly three times GCT. `parser.py` alone is 11,063 lines and `generator.py` is 6,898. Agents have to find their way in very large files. Each dialect is its own module.

**Written decisions: yes (Read).**

- `AGENTS.md` (521 lines; `CLAUDE.md` is an identical copy) explains the architecture.
- It also gives explicit rules. Examples:
  - "no-dependency … pure Python"
  - "Never suggest Pratt parsing as an optimization"
  - "Avoid Compile-Time NULL Checks"
  - "Don't add backwards-compatibility shims"
- There are also `CONTRIBUTING.md` and four explanatory posts.
- Only maintainers open pull requests. Outside users report issues (Read).

**Two cautions:**

- **AI-written commits (Script):** 232 of the 1,191 commits since July have `[CODEX]` or `[CLAUDE]` in the title. `AGENTS.md` asks agents to tag their commits that way. Prefer untagged fixes for replays (all of those below are untagged). Remove that tagging line from the practice copy, or every arm's commits will carry it.
- **Auto-loaded instructions:** `CLAUDE.md` would load into every run automatically, whatever the arm (Read). Delete `CLAUDE.md` from the practice copy and keep `AGENTS.md` as an ordinary project document. Then reading the project's rules stays a choice each arm makes.

**Replayable fixes (Read).** All pull requests were opened in November 2026. I left out fixes that also move the integration-test submodule (`d2de3ce`, `3ce7c4f`, `3721a79`).

| Commit | Merged | Bug | Files | Lines | Ticket source |
| --- | --- | --- | --- | --- | --- |
| `dc4afaf` | 2026-11-20 | Parser confuses a column named TOP with a row limit (Oracle, Snowflake, Redshift) | 5 | +29/-6 | PR #9295 → issue #9284 |
| `68ef75b` | 2026-11-20 | SQLite `UPDATE OR REPLACE` / conflict clauses not supported | 7 | +43/-8 | PR #9296 → issue #9281 |
| `41fce8b` | 2026-11-20 | SQLite `END` / `END TRANSACTION` not parsed as COMMIT | 3 | +57/-1 | PR #9297 → issue #9280 |
| `9951ad2` | 2026-11-19 | Snowflake unquoted stage paths and `file://` URIs split into many tokens | 5 | +169/-4 | PR #9243 → issue #9242 |
| `32fa2f1` | 2026-11-19 | Postgres `LEFT`/`RIGHT` with negative length translated wrongly | 3 | +15/-0 | PR #9219 (348 chars) |
| `947af87` | 2026-11-19 | Postgres `MAKE_DATE` not parsed or generated | 3 | +20/-0 | PR #9213 (1,084 chars) |
| `4441feb` | 2026-11-19 | Exasol `HASHTYPE` data types unsupported | 6 | +24/-0 | PR #9209 → issue #9199 |
| `f36da3f` | 2026-11-18 | `TRY_CAST` silently falls back to a lossy CAST with no warning | 4 | +19/-4 | PR #9197 → issue #9196 |
| `34ac378` | 2026-11-16 | Optimizer changes NULL behaviour when un-nesting `IN` subqueries | 3 | +32/-12 | PR #9151 → issue #9122 |
| `2359d11` | 2026-11-16 | Hive/Spark `DATEADD` drops millisecond and microsecond units | 3 | +26/-4 | PR #9161 → issue #9160 |
| `8802c5a` | 2026-11-16 | Spark `EXISTS(array, lambda)` loses its lambda when generated | 3 | +31/-1 | PR #9140 → issue #9032 |
| `ae3d013` | 2026-11-16 | Presto/Trino `AT TIME ZONE` on a zoneless value is wrong in BigQuery | 6 | +37/-7 | PR #9097 (1,647 chars) |
| `83d02ae` | 2026-11-16 | SQLite `GENERATE_SERIES` loses the exclusive end of a range | 3 | +11/-2 | PR #9123 (747 chars) |
| `913be7d` | 2026-11-16 | SQLite unary plus (a type-affinity trick) is dropped | 5 | +54/-0 | PR #9126 → issue #9124 |

**Replay dry run (Script).** At `41fce8b`'s parent, with only the fix's test file copied in, the SQLite tests show 4 failures. With the fix, they pass.

**Ticket ideas:**

- **Feature:** support one SQL function family end to end in three dialects that lack it. That means a new expression class, parser entries, generator entries and three dialect modules. Which function to use is Not checked.
- **Vague:** "Make the warnings sqlglot gives when a translation loses meaning easier to act on." The open decision is whether to warn, raise an error, or collect them for the caller.
- **Wrong request:** "When `COALESCE` gets a literal NULL argument, drop it during translation so the output is cleaner." This breaks the written rule "Avoid Compile-Time NULL Checks … NULL handling should happen at query time" (Read). A second option is a ticket to speed up the parser by rewriting it as a Pratt parser, which `AGENTS.md` forbids by name.

### urfave/cli (Go library for building command-line programs)

**Commands (Script; commit `d5c06cb`, 2026-11-10):** Go 1.26.11, unpacked into a scratch folder.

```
go mod download                    # one dependency (testify)
go test ./...                      # 2 s uncached; 657 top-level tests, all pass
```

**Size (Script):** about 8,300 product lines, a quarter of GCT. The largest file is 785 lines.

**Written decisions: yes (Read).** User documentation under `docs/v3/` states behaviour precisely. It changes in reviewed pull requests, for example `fe4bf00`, which documented that when a flag is given in two forms "the last value is used".

**Replayable fixes (Read).** These are merged pull requests from many outside contributors, with long descriptions (often 2,000 to 3,500 characters). I excluded `8f9865b` because its pull request was opened in November 2025, before the models' cutoff.

| Merge | Merged | Bug | Files | Lines | Ticket source |
| --- | --- | --- | --- | --- | --- |
| `8caec7d` | 2026-11-08 | Completion help shows the default command name, not the configured one | 3 | +15/-10 | PR #2512 (2,379 chars) |
| `724f6d4` | 2026-11-08 | Fish completion omits ancestors' persistent flags | 4 | +188/-0 | PR #2506 (3,263 chars) |
| `6d5074b` | 2026-11-08 | Help text wrapping counts bytes instead of characters | 2 | +15/-6 | PR #2511 (819 chars) |
| `431e2dc` | 2026-11-01 | `help a b` shows help for `a`, not `a b` | 2 | +68/-2 | PR #2520 (1,617 chars) |
| `293b022` | 2026-10-29 | Root command's Run arguments are not completed | 5 | +59/-173 | PR #2489 → issue #2486 |
| `89ad116` | 2026-10-26 | Flags allowed through `AllowExtFlags` are not reported as set | 8 | +233/-44 | PR #2503 (3,885 chars) |
| `a772405` | 2026-10-25 | Mutually exclusive flag groups not checked after dispatching to a subcommand | 2 | +90/-22 | PR #2497 → issue #2496 |
| `e03df0f` | 2026-10-24 | Running a command a second time keeps stale flag state | 3 | +71/-0 | PR #2491 (3,001 chars) |
| `3546945` | 2026-10-21 | A wrapped `ExitCoder` loses its exit code and message | 4 | +114/-8 | PR #2479 → issue #2478 |
| `f7659f8` | 2026-10-20 | Single-dash flags whose names start with a digit are not parsed | 2 | +116/-2 | PR #2474 (2,876 chars) |
| `3c3f9bb` | 2026-10-19 | Arguments after `--help` are treated as commands | 3 | +75/-11 | PR #2476 → issue #2126 |
| `63c2771` | 2026-10-25 | Deserializing null wipes slice or map flag destinations | 3 | +27/-3 | PR #2482 (1,985 chars) |

**Ticket ideas:**

- **Feature:** a new flag type (for example a URL flag) with parsing, help output, shell completion and documentation.
- **Vague:** "Make the help output easier to scan."
- **Wrong request:** "Make it an error to give the same flag in both its long and short form." The v3 docs say the last value wins, and that `OnlyOnce: true` is the opt-in way to make repeats an error (Read).

### jsoup (Java HTML parser)

**Commands (Script; commit `d90d575`, 2026-11-04):** Java 17 (already installed) and Maven 3.9.9, unpacked into a scratch folder.

```
mvn -B verify                      # 72 s first run including downloads; 2,256 tests, 0 failures
mvn -B -o verify                   # 25 s warm, offline (add the IPv4 setting inside a sandbox)
```

**Size (Script):** about 31,600 product lines, the same size as GCT.

**Written decisions: almost none in the repo (Read).** There is a short README, an 18-line contributing guide and a changelog. Behaviour follows the external WHATWG HTML standard and is pinned by tests.

**Caution (Read):** jsoup's contributing guide says the project does not accept code "generated in whole or part by AI". A practice copy sends nothing upstream, and the MIT licence allows it. But a public practice copy of a project that openly rejects AI work may not sit well with the owner.

**Replayable fixes (Read).** These are mostly the maintainer's own commits, many without an issue. Fixes are spec-heavy and often 4 or more files, which makes them meatier than Hono's.

| Commit | Merged | Bug | Files | Lines | Ticket source |
| --- | --- | --- | --- | --- | --- |
| `659b7d2` | 2026-11-04 | Cloning an element copies cached children through its attributes | 5 | +51/-8 | commit cites #2638 |
| `6feca03` | 2026-10-22 | `.empty()` leaves nested form controls attached to the form | 2 | +17/-6 | none (commit text only) |
| `76c125d` | 2026-10-22 | Selector parsing fails across buffer boundaries | 3 | +90/-2 | none |
| `0dc96b3` | 2026-09-29 | Comments and incomplete tags tokenised wrongly | 4 | +96/-44 | PR #2636 (469 chars) |
| `1aa1234` | 2026-09-29 | Malformed doctypes tokenised wrongly | 4 | +111/-17 | PR #2635 (435 chars) |
| `118acb6` | 2026-09-28 | Attribute equality includes internal data attributes | 4 | +84/-13 | commit cites #2633 |
| `8171849` | 2026-09-27 | The `/` of a malformed end tag is not consumed | 4 | +15/-2 | commit cites #2631 |
| `093e2f5` | 2026-09-24 | `<dialog>`, `<main>`, `<search>` do not close an open `<p>` | 3 | +14/-6 | commit cites an issue |
| `f79f21d` | 2026-09-24 | Double-escaped script tags close too early | 5 | +30/-5 | commit cites #2627 |
| `1eb02ea` | 2026-09-21 | `<template>` parsing wrong at end of file and with forms | 4 | +66/-27 | PR #2615 → issue #2614 |
| `cd22c55` | 2026-09-07 | Named entities before `-` and `_` in attributes not decoded | 4 | +49/-2 | PR #2596 → issue #2588 |
| `66be2da` | 2026-08-22 | Redirects to single-slash locations resolve wrongly | 4 | +16/-2 | PR #2580 (82 chars) |
| `dd35567` | 2026-08-01 | HTTP client fails on responses without Content-Type | 4 | +19/-2 | PR #2549 (empty) |
| `4e38114` | 2026-07-26 | Redirect method handling does not follow RFC 9110 | 4 | +195/-15 | none |

**Ticket ideas:**

- **Feature:** a Safelist option to allow `data-*` attributes by prefix in the cleaner (whether this already exists is Not checked).
- **Vague:** "Make pretty-printed output look nicer around inline elements."
- **Wrong request:** "Keep the `<p>` open when a `<main>` starts inside it." Fix `093e2f5` deliberately closes it, following the HTML standard, and tests pin it.

### goldmark (Go Markdown parser)

**Commands (Script; commit `48a280d`, 2026-11-19):**

```
go test ./...                      # 5 s; 66 top-level tests, 737 with spec examples
go test -skip TestDoc ./...        # the offline form; TestDoc downloads a tool
```

**Size (Script):** about 16,700 product lines, with no dependencies. Tests are mostly spec examples stored in `.txt` files.

**Written decisions: yes (Read).** The CommonMark spec is the contract, enforced by its example suite. The README has a table of options and defaults. `AGENTS.md` (56 lines) gives coding rules, and `CLAUDE.md` just points to it.

**Replayable fixes (Read).** Nearly all fix a numbered issue, and the issue texts are long (about 1,000 to 4,200 characters). Fixes are small: usually one source file plus a spec example.

| Commit | Merged | Bug | Files | Lines | Ticket source |
| --- | --- | --- | --- | --- | --- |
| `1bd9416` | 2026-11-11 | HTML block parsing | 3 | +68/-8 | issue #643 |
| `3e5e85c` | 2026-11-12 | HTML block parsing | 2 | +13/-0 | issue #647 |
| `c3f9391` | 2026-11-11 | List parsing | 2 | +53/-1 | issue #645 |
| `9e4c172` | 2026-11-11 | Block AST | 2 | +59/-3 | issue #644 |
| `04fa52b` | 2026-11-03 | Linkify extension | 2 | +18/-0 | issue #639 |
| `50b2edc` | 2026-11-03 | HTML block parsing | 2 | +27/-2 | issue #637 |
| `66ec827` | 2026-11-03 | HTML block and raw HTML | 3 | +15/-3 | issue #636 |
| `eed7e7b` | 2026-11-03 | Link parsing | 3 | +47/-0 | issue #631 |
| `ea9b18e` | 2026-10-31 | Definition list and task list extensions | 5 | +62/-20 | issues #620, #621 |
| `9ac8030` | 2026-10-21 | Emphasis delimiters with linkify | 2 | +22/-15 | issue #613 |
| `e734800` | 2026-10-25 | Table parsing when a delimiter-like row follows a table | 2 | +35/-4 | commit cites #611, #588 |
| `ec084e4` | 2026-10-21 | Emphasis fast path mishandles linkify prefixes | 4 | +158/-51 | none |
| `4dd635b` | 2026-09-10 | Indented code blocks with tabs | 3 | +105/-17 | commit cites #583 |

(The "Bug" column gives the area only. The details are in each issue, which I did not summarise.)

**Ticket ideas:**

- **Feature:** a `==highlight==` extension with an AST node, an inline parser, an HTML renderer and an option (whether one exists is Not checked).
- **Vague:** "Make line breaks behave better for Japanese text."
- **Wrong request:** "Render single newlines as `<br>` by default." The CommonMark spec treats them as soft breaks, and the README documents `WithHardWraps` as the opt-in.

### ripgrep (Rust command-line search tool)

**Commands (Script; commit `4a51093`, 2026-11-22):** Rust 1.100 (cargo 1.100.0), installed with rustup into a scratch folder.

```
cargo test --workspace             # 20 s first build and test; 6 s after; 1,377 pass, 3 ignored
```

**Size (Script):** about 52,000 lines including tests written inside source files. That makes it larger than GCT.

**Written decisions: some (Read).** `FAQ.md` and `GUIDE.md` state firm choices. For example, ripgrep "is a search tool that will never touch your files".

**Cautions:**

- **AI policy (Read):** `AI_POLICY.md` bans autonomous agents from contributing upstream. A practice copy sends nothing upstream.
- **Hidden tests in source files (Read):** many fixes add their tests inside the same source file as the fix. The grader would have to copy test blocks into product files.
- **Memorisation (Read; Not checked):** three fixes close issues from 2021–2024 (`3860ead`, `9ca85a3`, `41d3959`). Earlier attempts at those fixes may have been public before the cutoff.

| Commit | Merged | Bug | Files | Lines | Ticket source |
| --- | --- | --- | --- | --- | --- |
| `76b7708` | 2026-11-21 | Compressed files detected by extension only, not content | 3 | +195/-16 | issue #3342 |
| `e8b49b6` | 2026-11-20 | `-g !DIRNAME/` fails when the current folder is DIRNAME | 3 | +68/-1 | PR #3581 → issue #1764 |
| `991405e` | 2026-11-19 | `-v -m N -A k` prints the rest of the input as matches | 3 | +131/-34 | issue #3593 |
| `9ca85a3` | 2026-11-20 | Ignored broken symlinks reported when following links | 2 | +165/-0 | issue #2552 (2023) |
| `4d592f1` | 2026-11-20 | Buffered matches lost after a parallel search error | 2 | +67/-49 | issue #3382 |
| `b466c0b` | 2026-11-21 | A lone `!` line in .gitignore misbehaves | 2 | +33/-0 | issue #3527 |
| `3860ead` | 2026-11-21 | `--json` emits one match per line in multiline mode | 2 | +270/-35 | issue #1983 (2021) |
| `9c49a25` | 2026-11-22 | Multiline match discovery stops at a look-ahead limit | 2 | +40/-7 | issue #3503 |
| `8bc7a7a` | 2026-11-21 | Trailing spaces in gitignore patterns parsed wrongly | 1 | +52/-5 | issue #3477 |
| `42a4be1` | 2026-11-21 | Symlink loops above the search root not detected | 2 | +113/-4 | PR #3534 |
| `41d3959` | 2026-11-20 | Glob character classes match the path separator | 2 | +90/-15 | issue #2745 (2024) |
| `1090d50` | 2026-11-19 | Tilde expanded anywhere in `core.excludesFile` | 2 | +67/-7 | PR #3592 → issue #3591 |
| `fdf7d95` | 2026-11-18 | Ignore files stop being read after an invalid UTF-8 line | 1 | +27/-2 | PR #3605 → issue #3604 |

**Ticket ideas:**

- **Feature:** a summary line with total matches and files at the end of normal output (whether one exists is Not checked).
- **Vague:** "Make output easier to use when piped into another program."
- **Wrong request:** "Add `--in-place` so `--replace` writes back to the files." The FAQ rules this out in plain words.

### mvdan/sh (Go shell parser, formatter and interpreter)

**Commands (Script; commit `95154f9`, 2026-11-18):**

```
go test ./...                      # 7 s; 167 top-level tests, about 25,000 sub-cases; 684 skipped
```

Some tests compare against a real bash or other shells and skip when those are missing (Read: `AGENTS.md`). Five tests fail inside the sandbox (see above).

**Written decisions: yes (Read).** The README has a "Caveats" section. There is a 645-line `doc/plan-v4.md` and an `AGENTS.md`, which `CLAUDE.md` copies.

**Why it ranks low (Read):** most fixes are tiny (2 files, often under 30 lines) and have no issue or pull request text. Tickets would have to come from one-line commit messages.

| Commit | Merged | Bug | Files | Lines | Ticket source |
| --- | --- | --- | --- | --- | --- |
| `3c1ff2a` | 2026-08-31 | `<<-` heredoc indentation wrong at deeper nesting | 2 | +2/-1 | none |
| `b5502bf` | 2026-08-31 | Nested heredoc indentation | 2 | +8/-0 | commit cites #1403 |
| `019025c` | 2026-08-31 | zsh short parameter prefixes with no name following | 3 | +19/-13 | commit cites #1405 |
| `502ecf9` | 2026-08-22 | Tracing of `let` clauses | 2 | +34/-23 | none |
| `47076bc` | 2026-08-22 | Crash when StopAt meets a refilled read buffer | 2 | +11/-2 | none |
| `1630417` | 2026-07-27 | Missing parameter name panics instead of erroring | 4 | +50/-2 | commit cites #1363 |
| `4bb620a` | 2026-07-26 | `getopts` ignores attached option arguments | 2 | +25/-16 | none |
| `a56bb30` | 2026-07-25 | Several wrong `Node.End` positions | 2 | +25/-10 | none |
| `42791fc` | 2026-07-23 | Zero padding and negative steps in brace sequences | 3 | +28/-26 | none |
| `52cf743` | 2026-07-23 | Arithmetic integer parsing and negative exponents | 2 | +53/-6 | none |
| `fcbbd45` | 2026-07-23 | Escaped characters inside bracket expressions | 2 | +37/-2 | none |
| `cbea6be` | 2026-07-27 | Unsupported zsh syntax panics instead of erroring | 3 | +15/-0 | none |
| `59f2be5` | 2026-07-26 | `type` builtin error message prefix | 2 | +3/-2 | none |

**Wrong-request idea:** "Make shfmt treat `${array[some string]}` as a string key." The README's Caveats section says the parser must assume an arithmetic index.

## What I ruled out without cloning

Screened with the GitHub API on 2026-11-22 (**Script**): licence, language, and the number of commits since 2026-07-01 ("fix-like" counts commit titles mentioning fix or bug).

- **pallets/click** (Python, 12,800 lines): only about 20 merged pull requests since July change code and tests together, and it repeats GCT's language at a smaller size.
- **pytest-dev/pytest** (Python, 40,000 lines): about 23 paired fixes since July. sqlglot covers "bigger Python" with far more.
- **junegunn/fzf** (Go): 17 fix-like commits; the full suite needs tmux and Ruby (per `codebases.md`).
- **go-chi/chi** (Go): 34 commits since July, 4 fix-like.
- **spf13/cobra** (Go): 1 commit since July.
- **stretchr/testify** (Go): 16 commits, none fix-like.
- **goccy/go-yaml** (Go): no commits since July.
- **expr-lang/expr** (Go): 23 commits.
- **charmbracelet/lipgloss** (Go): 29 commits.
- **charmbracelet/bubbletea** (Go): 53 commits; Go is already covered by three tested candidates.
- **labstack/echo** (Go): 85 commits, 27 fix-like; Go is already covered.
- **go-playground/validator** (Go): 42 commits.
- **colinhacks/zod** (TypeScript): cloned, then cut (needs the Nub installer; see above).
- **unjs/h3** (TypeScript): active (286 commits), but the same kind of project as Hono. It is the natural swap if Hono falls through.
- **open-circle/valibot** (TypeScript): 70 commits; Hono covers TypeScript with far more history.
- **sindresorhus/ky** (TypeScript): a very small library, so tickets would be too small.
- **toss/es-toolkit** (TypeScript): fixes are single utility functions, too small.
- **remeda/remeda** (TypeScript): same reason.
- **markedjs/marked** (TypeScript): GitHub cannot read its licence ("NOASSERTION"), so it needs a closer look; Hono already covers TypeScript.
- **date-fns/date-fns** (TypeScript): 15 commits; no licence detected by GitHub.
- **iamkun/dayjs** (JavaScript): 12 commits.
- **tj/commander.js** (JavaScript): 44 commits, 6 fix-like.
- **eemeli/yaml** (TypeScript): 40 commits, 7 fix-like.
- **NaturalIntelligence/fast-xml-parser** (JavaScript): 10 fix-like.
- **BurntSushi/jiff** (Rust): 33 fix-like and strong design docs; ripgrep already covers Rust. Worth a look if the owner wants Rust with more writing.
- **casey/just** (Rust): CC0 licence, 6 fix-like.
- **Textualize/rich** (Python): 10 commits since July.
- **encode/httpx** (Python): 4 commits.
- **python-attrs/attrs** (Python): 8 fix-like.
- **python-jsonschema/jsonschema** (Python): 4 fix-like.
- **pyparsing/pyparsing** (Python): 38 commits.
- **pytest-dev/pluggy** (Python): 5 fix-like.
- **andialbrecht/sqlparse** (Python): 32 commits.
- **python-humanize/humanize** (Python): tiny.
- **fastapi/typer** (Python): 3 fix-like.
- **dateutil/dateutil** (Python): 10 fix-like; dual licence.
- **more-itertools/more-itertools** (Python): fixes are single functions.
- **sdispater/tomlkit** (Python): 19 fix-like, small. Untested; a possible "small Python" option.
- **pypa/packaging** (Python): small and governed by written standards (PEP 440/508), with 61 fix-like commits. Untested, and GitHub reports its dual licence as "NOASSERTION". Worth a look if the owner wants a small Python project with strong written rules.

## Recommendation

**1. Hono (TypeScript, about GCT's size, almost nothing written down).**

- It changes the language and keeps the size. That isolates the question "does the way of working travel to another language?"
- It is the cleanest test of whether "check the ask" still helps when the only record of a decision is a test.
- The tests are fast (20 seconds), and there are dozens of fresh fixes, each tied to a written issue.
- Trade-offs:
  - Fixes are small, so pick from the larger ones listed above.
  - The harness must either allow the npm registry or install packages before each run. Installing first worked offline here.
  - Its tools (pnpm 12, vite-plus) are newer than the models.

**2. sqlglot (Python, nearly three times GCT's size, with explicit written rules).**

- It changes the size and keeps the language. Agents must work in an 11,000-line parser and dozens of dialect modules they cannot read end to end.
- Its `AGENTS.md` has plain "never do this" rules, which suit wrong-request tickets.
- It needs no harness change at all (PyPI only), and the tests take 36 seconds.
- Trade-offs:
  - It is Python again, so it says nothing about other languages.
  - About a fifth of its recent commits were written by AI agents. Use untagged fixes only.
  - Its `CLAUDE.md` should be removed from the practice copy so it does not load into every arm.

Together the two differ from GCT and from each other in language, size and how much is written down.

**Reserve: urfave/cli (Go, a quarter of GCT's size, behaviour written in its docs).**

- It can stand in for either pick: another language for Hono, or written rules for sqlglot.
- Its tests run in 2 seconds, and its fixes come from many outside contributors with long pull request descriptions.
- Trade-offs: the harness needs the Go toolchain and the Go module proxy. Small size means tickets may run short of the 5-to-30-minute range.
- If the owner specifically wants a second "almost nothing written" codebase instead, jsoup is the next choice, with the AI-policy caution above.

## What I could not check

- **Whether the run sandbox can read caches outside the repo** (Not checked). Maven, Go and Cargo keep downloads in the home folder. Hono and sqlglot avoid the question because their packages live inside the repo.
- **How Claude Code's own sandbox handles IPv6 localhost and special file permissions** (Not checked). These broke jsoup and mvdan/sh under the plain macOS sandbox. Run the harness smoke test before freezing.
- **Ticket difficulty** (Not checked). Lines changed are a rough guide. No agent has attempted these fixes yet. The ticket author should time a few.
- **Memorisation beyond dates** (Not checked). I checked that pull requests were opened after 1 July for Hono, sqlglot, jsoup and urfave/cli. For goldmark, mvdan/sh and ripgrep I checked only merge dates and the issues' opening dates.
- **Whether the ticket ideas are feasible** (Not checked). They are pointers, not frozen tickets.
- **Whether Hono's suite needs Bun** (Not checked). Bun was already installed here.
- **Whether sqlglot's integration-test submodule is public** (Not checked). Not needed with `SKIP_INTEGRATION=1`.
- **Ticket text quality** (Not checked). Issue texts were counted by length, not read in full. The ticket author must strip fix hints from them.

## How this was done

1. I screened 46 repositories with the GitHub API.
2. I made shallow clones of 10 (history since 2026-05-01) and paired post-July commits that change code and tests with a script.
3. I ran the test suites of 7. Every toolchain went into a scratch folder inside this worktree: Go 1.26.11 from go.dev, Maven 3.9.9 from archive.apache.org, and Rust via rustup from static.rust-lang.org. All caches were pointed into that folder too. Nothing was installed system-wide.
4. I read issue and pull request metadata with `gh api`.
5. The clones, tools and caches were deleted afterwards.
