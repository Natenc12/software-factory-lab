# How the owner worked with coding agents on grounded-class-tutor, 21 November 2026

Covers the owner's sessions on `grounded-class-tutor` from 05:00 on 21 November to 07:00 on 22 November (local
time, UTC−5), from the transcripts, 57 helper-agent logs, the GitHub pull requests and the `work-ticket` skill and
notes. Nothing in the project was run or changed. Tags: **[Script]** counted with a script, **[Read]** read by me, **[Not checked]**.

## 1. The day in numbers

- **Sessions:** three. An orchestrator ran the ticket board (`25ca9302…`, 48 helper agents). An overnight triage ran
  in `497f1de8…` (9 helpers). An older session got two messages about planning this experiment (`bee64b64…`).
  [Script] Seven other sessions that day were unrelated and left out. [Read]
- **Pull requests:** 16 opened and all 16 merged, 14 the same evening and 2 the next morning. CI was green on every
  one at merge. None was reverted, and none needed a follow-up fix PR. [Script] One slip: #242's description said
  "closes #198", so the merge closed that ticket by mistake. The agent reopened it 16 seconds later. [Script]
- **Owner messages:** 45 typed, 40 of them to the orchestrator, plus 9 shell commands the owner ran. [Script]
- **Tokens (input + output + cache writes):** 16.3M in all. The orchestrator and its helpers used 13.6M. The 16 PRs
  took 10.6M of that, about 660k each: builders 6.6M, reviewers 2.4M, explainer videos 1.7M. [Script]
- **Speed:** the median time from a builder starting to its merge was 43 minutes for the same-evening PRs (range 9
  to 91). [Script]

## 2. How the owner actually works

**Short go-aheads.** 25 of the 40 messages to the orchestrator were five words or fewer: 14 merge words and about 10
"Yes, …" approvals. [Script] For example, `25ca9302…` at 19:04: "Label added, merge".

**The agent writes the spec and the owner approves it.** All three sessions opened with a rough request of one or two
sentences. `25ca9302…` began, at 16:02, with "orchestrate the ticketboard". [Read] Yet all 16 tickets that got built
were full specs of 382 to 1,538 words, each with "Done when" and out-of-scope lists. [Script] Agents drafted them,
and the owner approved them in four batches: the #210 rewrite, stage 0 ("Yes, post it", 16:59), stage 1 ("Yes, go
ahead", 18:44), and the Python ticket. [Read]

**The owner catches errors the agent should have caught.** This happened five times in one evening. [Read]
- The agent recommended building on the October version of the app. The owner, at 16:36: "The october build wasnt
  engineered though if i remember correctly".
- The plan recommended building #192. Only after the owner asked what it was worth (16:14) did the agent find that
  14 of its 18 fixes were in code about to be retired.
- On #183 the agent treated deliberate attacks as blocking. The owner, at 18:23: "who attacks their own desktop app?"
- The agent asked the owner to merge two high-risk PRs without the brief its own skill requires. The owner, at 17:15:
  "give me the merge briefs for both".
- Agents were working one ticket at a time. The owner, at 20:09: "are you only able to do one ticket at a time?"

**The owner keeps asking for simpler reports.** Five times on the 21st: plain English (16:12), "something tangible to
tie it to" (16:14), use the explainer skill (19:54), better videos (20:28), and videos instead of merge briefs
(21:24). The same complaint came three times on the 20th, though the skill already said "visual first, plain
English". [Read]

**The owner does the hands-on steps.** Of the owner's 9 shell commands [Script], two were checks only the owner could
run: the spike demo, and a live Claude test on their own Mac login. The other seven repaired their own checkout
after the Python upgrade, because it sat on an old branch 14 commits behind. [Read]

## 3. Where the owner's attention went

The owner answered about 35 orchestrator stops. Their other 5 messages came while agents were still working. [Read]
My judgement on each kind of stop:
- **Needed:** about 10 plan or batch approvals, and the 14 merge words. But the merge words came one at a time over 6
  hours.
- **Avoidable:** adding the `owner-ok` label on GitHub, done before 10 of the 14 merges, plus one extra trip when a
  label had not stuck. The owner called it "annoying" (21:39), and #241 removed it. Also avoidable: one request for a
  skipped brief, two format complaints, and two waits for a video ("where is the video", 22:11).
- **Needed stop, agent's error:** the four direction corrections, which mostly inside other replies.

By count, approving merges cost the most. It took about 27 owner actions (14 merge messages, about 10 label visits,
3 chases) to approve 14 PRs whose CI was already green. [Read] The costliest single miss was #183 (PR #223). The
over-strict threat model sent it through four review rounds: 1.26M tokens, the most of any same-evening PR, and 82
minutes. [Script]

The overnight triage rightly asked nothing after its first three messages. In the morning it reported that a hook
had blocked three prototype commits and that one test had pinged an outside library's maker. [Read]

## 4. Compared with the stage 1 findings

**Already in line with the experiment:**
- **Fuller tickets.** In stage 1, a rough ticket sank the bare agent. The owner's flow turns every rough request into
  a full spec before anything is built. [Read]
- **Honest status claims.** Stage 1's bare agent mostly failed through false claims in its own report. The owner's
  skill reserves "verified" for CI and makes every claim say who checked it. A rough script flagged 11 of 60 helper
  reports; the 4 flagged builder reports I read each had a CI check the script had missed. [Script, Read]
- **A fresh reviewer.** Reviewers found blocking problems in 5 of the 15 PRs they reviewed. One was a failed save
  that was never undone, on #232. [Script, Read] In stage 1 a reviewer did not raise trust, but the practice tickets
  there were much smaller.

**What the experiment suggests changing:**
- **Weight.** About 660k tokens per PR is nearer stage 1's five-role team (580k a run) than its one-page guide (80k).
  Real PRs were bigger (up to 3,019 added lines), so this is not like for like. [Script] Each PR passes builder,
  reviewer and often a video maker; in stage 1, heavier fixed processes did not beat the guide. [Read]
- **Wrong-direction work.** In stage 1, no agent questioned a ticket that asked for the wrong thing. Here, too, it
  was the owner who caught all three direction errors (the October version, #192, #183). [Read]
- **Owner reading.** PR descriptions ran to 879–2,475 words on 7 PRs [Script], like the heavier stage 1 arms
  (2,300–2,800 words a ticket), with a video on top.

## 5. Suggestions, ranked by attention or trust saved

1. **Check "is this worth it, and the right direction?" before the plan stop.** Before asking the owner anything, the
   builder answers three fixed questions: what of this survives the planned direction, how any code it reuses was
   made, and what realistic bad input looks like for a personal desktop app. These would have caught #192, the
   October version and #183. The lessons are in `NOTES.md`; make them a required step.
   *Saves trust and the costliest rework.*
2. **Ask about merges in batches, with the evidence in the ask.** When PRs are ready, send one message with a line per
   PR, its risk, its video link, and "merge all, or pick". The morning's "Merge both" cleared two PRs at once, where
   the evening took 14 separate trips. Keep the label off. *Saves about half the stops.*
3. **Fold the skill and its notes into one page,** with the owner's reporting rules and the threat model at the top.
   Stage 1's best arm was a one-page guide, and the reporting complaint came back on both days although the rule was
   written down. *Saves repeat corrections and builder tokens.*
4. **Match the ceremony to the risk.** A 44-line fix (#231) went through the same build-and-review path as a 1,265-line
   new store. Eight videos cost 1.7M tokens, about a tenth of the day. Make one video per batch, and skip review for
   small low-risk changes, as already happened for the README PR. *Saves tokens, with little trust lost.*
5. **Make owner-run steps one command, and check the owner's checkout first.** Seven of the owner's nine shell
   commands were repairs to an out-of-date checkout. And the OpenAI key a reviewer printed into its log was still not
   replaced the next morning; keep it on the owner's list until it is. *Saves small but annoying attention.*

## 6. What I could not check

- Whether the merged code is right beyond CI and review. Only a day has passed, so fix PRs may still come.
  [Not checked]
- How long the owner spent reading or watching. I have message counts and times only. [Not checked]
- What the overnight triage changed on GitHub after 07:00. [Not checked]
- Every agent claim. I script-checked the helpers' reports, read 4, and did not check the orchestrator's messages to
  the owner. [Not checked]
- Dollar cost. Cache reads were left out by design, and they were large: 196M for the orchestrator alone. [Script]
- Helper agents' effort level. The main sessions logged "high"; helpers do not log it. [Not checked]

## Sessions and pull requests

Model and effort: the orchestrator ran on Fable 5.2 with high effort and auto permissions, and its helpers on Opus 5.5
(four small doc lookups ran on Haiku 5.5). The other two sessions ran on Opus 5.5 with high effort. No session used
plan mode. The process in force was the `work-ticket` skill (two fixed stops, a fresh reviewer, merge only on the
owner's word) and, for the triage session, the `triage` skill. [Script, Read] "Start" is when the builder or intake
agent began. Every ticket was a full spec. [Script]

| Session or PR | First ask (spec) | Owner messages for it | Avoidable owner work | Tokens | Start → PR / merge | Outcome | Owner caught |
|---|---|---|---|---|---|---|---|
| `25ca9302…` orchestrator, "gct tickets" | "orchestrate the ticketboard" (rough) | 40 typed, 9 shell | 6 extra trips, plus label visits on 10 merges | 13.63M incl. helpers | 16:02 → first PR 16:28 | 16 PRs, all merged | 5 (section 2) |
| `497f1de8…` overnight triage | triage the board using leftover usage (rough) | 3 | 0 | 2.11M | no PR | drafts applied next morning [Not checked] | none |
| `bee64b64…` (21st only) | write a handover for this experiment (rough) | 2 | 0 | 0.58M | no PR | led to this lab's kickoff | none |
| PR #215 synthetic course | #199 (full) | 2 | 0 | 795k | 25m / 44m | merged, green | #192 not worth building |
| PR #220 README | #217 (full) | 1 | 0 | 83k | 2m / 9m | merged, green, no review | none |
| PR #221 move shared type | #219 (full) | 2, shared with #222 | 2 (brief, label) | 263k | 5m / 19m | merged, green | briefs skipped |
| PR #222 risk rules | #218 (full) | shared with #221 | shared | 185k | 5m / 17m | merged, green | briefs skipped |
| PR #223 safe parsing | #183 (full) | 1 | 0 (but 4 review rounds) | 1,258k | 12m / 82m | merged, green | threat model too strict |
| PR #231 label guard | #224 (full) | 1 | 1 (label) | 195k | 6m / 28m | merged, green | none |
| PR #232 library schema | #226 (full) | 1 | 1 (label) | 743k | 10m / 42m | merged, green; reviewer blocker fixed | none |
| PR #233 Claude provider | #225 (full) | 1, plus a live test run by hand | 1 (label) | 832k | 12m / 51m | merged, green | none |
| PR #234 library documents | #227 (full) | 2 | 1 (label) | 359k | 8m / 31m | merged, green | none |
| PR #235 keyword search | #228 (full) | 2 | 1 (label) | 631k | 10m / 61m | merged, green | none |
| PR #236 import | #229 (full) | 1 | 1 (label) | 854k | 11m / 65m | merged, green; reviewer blocker fixed | none |
| PR #237 ask | #230 (full) | 2 | 1 (video chase) | 759k | 9m / 76m | merged, green | none |
| PR #239 Python 3.14 | #238 (full) | 3 | 1 (label) | 917k | 67m / 91m | merged, green; owner repaired checkout | none |
| PR #241 risk gate | #240 (full) | 4 | 3 (video wait, label twice) | 305k | 5m / 28m | merged, green | label was friction |
| PR #242 record and replay | #198 (full) | 1, shared with #243 (next morning) | 0 | 1,193k | 7m / next morning | merged, green; wrongly closed #198, reopened | none |
| PR #243 drive command | #188 (full) | shared with #242 | 0 | 1,234k | 10m / next morning | merged, green; reviewer blockers fixed | none |

Tokens for each PR add up its builder, reviewer and video agents. "Owner messages for it" and "avoidable owner work" come
from reading the transcript. [Script for tokens and times; Read for messages and stops]
