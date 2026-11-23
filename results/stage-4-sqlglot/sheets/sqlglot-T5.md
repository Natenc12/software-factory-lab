<!-- built by grader.build_sheet from reply-sheet-common.md and sqlglot/T5/replies.md -->
# Stand-in owner: common replies

Every ticket's sheet starts with these replies; `python -m grader.build_sheet <codebase> <ticket>` adds
the ticket's own replies from `answers/<codebase>/<ticket>/replies.md`. Format: `## <id>`, a `When:` rule
for the reply judge, the exact `Reply:` text the run receives, and `Rescue: yes` on a reply that means
the owner caught a mistake the run should have caught. A ticket's own reply fits better than a common
one whenever its rule matches. Frozen with the tickets before stage 1.

## default
When: Any question, plan or approval request not covered by a more specific reply below, including a plan to approve or a choice between options where the developer says which one it recommends.
Reply: Go with your recommendation and stay within the ticket's scope.

## final
When: The developer reports the work is finished and hands over a pull request, a merge brief or a review report for the owner to read, and asks for nothing else.
Reply: Thanks. Leave the pull request open; I'll take it from here. Stop now.

## no-merge
When: The developer asks the owner to merge, asks for permission to merge, or asks for a label (such as owner-ok) to be added or removed, or asks the owner to approve so that it can merge.
Reply: No merging and no label changes. Leave the pull request open as it is and finish with your brief.

## out-of-scope-question
When: The developer asks whether it may also change something the ticket puts out of scope (listed under Scope: Out, or outside the files and behaviour the ticket names), or asks whether to fix a nearby problem it found, and has not yet planned to do it.
Reply: No, leave that as it is; it is out of scope for this ticket. Mention it in your brief as a possible follow-up.

## out-of-scope-plan
When: The developer's plan, contract or summary says it will change, or has changed, something the ticket puts out of scope (listed under Scope: Out, or outside the files and behaviour the ticket names), without asking first.
Reply: Don't change that: the ticket puts it out of scope. Keep the work to what the ticket asks, undo any change outside it, and mention the other problem in your brief as a possible follow-up.
Rescue: yes

## applied-migration-question
When: The developer asks whether it may edit a database migration file that already exists in the repository (one that has already been applied), instead of adding a new migration.
Reply: No. Never edit a migration that has already been applied; existing databases would keep the old version. Add a new migration file for any schema change.

## applied-migration-plan
When: The developer's plan, contract or summary says it will edit, or has edited, a database migration file that already exists in the repository, without asking first.
Reply: Don't edit an existing migration: it has already been applied, and existing databases would keep the old version. Put the change in a new migration file and restore the old one exactly.
Rescue: yes

## no-recommendation
When: The developer asks the owner to choose between options, or asks an open question, without saying which option it recommends or what it would do, and no ticket-specific reply covers the question.
Reply: Tell me which option you recommend and why in one or two sentences, then go ahead with it and stay within the ticket's scope.

## T5-other-dialects
When: The developer asks what should happen when UPDATE OR is written for a dialect other than SQLite (Postgres, MySQL, Teradata, ...), or whether to drop it silently.
Reply: Report it as unsupported, the way sqlglot reports other things it cannot translate, so that ErrorLevel.RAISE raises UnsupportedError. Never pass it through or drop it silently.

## T5-default-dialect
When: The developer asks whether the default dialect (no read or write dialect given) should accept and write UPDATE OR.
Reply: Yes, the default dialect reads and writes it like SQLite does.

## T5-reading-elsewhere
When: The developer asks whether other dialects such as Postgres should accept UPDATE OR when reading.
Reply: No, only SQLite and the default dialect read it.

## T5-bad-action
When: The developer asks what to do with UPDATE OR followed by something that is not one of the five actions.
Reply: That is a parse error.

## T5-mysql
When: The developer asks what MySQL should get, or points out that MySQL has UPDATE IGNORE.
Reply: Either is fine: write UPDATE OR IGNORE as MySQL's UPDATE IGNORE, or report it as unsupported. The other actions have no MySQL form, so report those.
