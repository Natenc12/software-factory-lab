# Stage 4 codebase shortlist

Research agent, 2026-11-21. GCT is about 32k lines of Python with Postgres. These candidates differ in language, size or both.

**Recommendation: jsoup (Java) first, Hono (TypeScript) second.** ripgrep (Rust) is the pick if the owner wants harder tickets over fast setup.

## How the numbers were taken (Script, 2026-11-21)

- Metadata (language, licence) from the GitHub API.
- Shallow clones (history since 2025-06-01). Line counts are raw `wc -l` over tracked source files, so they include blanks and comments. Test files are separated by path.
- "Tests" is an approximate count of test markers (`@Test`, `#[test]`, `it(`/`test(`, `func Test`, `def test_`).
- "CI test time" is the duration of one main test job in the latest successful GitHub Actions run. It includes setup and compile.
- **Replay pairing:** commits since 2026-03-01, excluding merges, whose message matches fix/bug/regress, and how many of those touch both product code and tests. A paired commit can become a history-replay ticket: reset to its parent, write the ticket from the linked issue or PR, and use its tests as hidden tests.

These are rough screens. The ticket author should still check each chosen commit by hand.

## The shortlist

| Repo | Language | Product lines | Test lines | Tests | CI test time | Licence | Commits since Mar 2026 | Fix commits with tests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [jhy/jsoup](https://github.com/jhy/jsoup) | Java | ~31,600 | ~34,400 | ~1,980 | 47–126 s per JDK/OS | MIT | 211 (149 by the maintainer, 60 bots) | 52 of 79 (49 cite an issue or PR) |
| [honojs/hono](https://github.com/honojs/hono) | TypeScript | ~30,600 | ~65,100 | ~3,190 | ~30 s (Node job) | MIT | 398, 99 authors | 162 of 171 `fix:` commits add a test file |
| [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | Rust | ~49,800 (includes inline tests) | ~6,600 in `tests/`, plus inline | ~880 | ~1 min incl. compile | Unlicense or MIT | 131, 59 authors | 10 of 13 `fix:` commits add a test |
| [junegunn/fzf](https://github.com/junegunn/fzf) | Go (plus Ruby integration tests) | ~27,300 | ~7,100 Go | ~610 Go | ~7 min (tmux integration suite) | MIT | 257, 25 authors | 35 of 93 |
| [pallets/click](https://github.com/pallets/click) | Python | ~14,000 | ~16,500 | ~640 | ~20–40 s | BSD-3-Clause | 230, 40 authors | 32 of 60 |

Dropped: `go-chi/chi` (Go, ~5.9k lines, MIT). It has good pairing (15 of 17), but only 40 commits since March, too few fresh replays.

## Why each fits, and the catch

**jsoup (recommended first).** A different language at the same size as GCT, so a result there isolates "does it generalise across languages" from "across sizes". It is an HTML parser that follows a long spec, so fixes have real edge cases and need care. One maintainer writes clean commits that bundle each fix with its test and cite the issue. The suite runs in about a minute. *Catch:* almost all commits come from one person, so issue threads are the main source for ticket text, with little PR discussion. Strip any fix hints from them (see report finding 3). Needs a JDK and Maven in the sandbox.

**Hono (recommended second).** A TypeScript web framework with fast tests and very consistent history: `fix(scope): what (#PR)`, with a test in nearly every fix. It has many contributors, so ticket texts vary in style like real work. *Catch:* fixes are small (on average 2.7 files and 55 added lines across 40 recent fixes). Race 1 showed that easy tickets can't tell the arms apart, so pick the larger replays. Use Hono's middleware and router for the multi-file feature ticket.

**ripgrep (alternate, for harder tickets).** Rust, larger, performance-sensitive, and strictly maintained. Its tests often sit inside the source files, so "fix with tests" means added `#[test]` blocks, which still works as hidden tests if the grader copies them in. A batch of fix PRs merged on 2026-11-21 gives very fresh replays. *Catch:* compile time slows every run's test loop, and its licence is Unlicense/MIT dual (fine for private use).

**fzf.** Go, popular, active. *Catch:* its full suite needs tmux and Ruby and takes about 7 minutes, and only about a third of fixes carry tests.

**click.** Pairs well and runs fast, but it is Python like GCT. It only tests a smaller size, not a different language. Keep it as a fallback if the owner prefers to change one thing at a time.

## A must for any open-source repo: pick commits newer than the models

All five are famous, so older commits and their fixes are likely in the models' training data. OpenAI found frontier models could reproduce original SWE-bench fixes word for word ([OpenAI](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/), read 2026-11-21). SWE-rebench guards against this by dating tasks against model release dates ([Nebius](https://nebius.com/blog/posts/introducing-swe-rebench), read 2026-11-21). The orchestrator should look up the training cutoff that Anthropic states for Opus 5.5 and Fable 5.2, and take replays only from after it. Fix-like commits since 2026-07-01: Hono about 160, jsoup about 61 (some are dependency bumps), ripgrep about 43, fzf about 42, click about 12.
