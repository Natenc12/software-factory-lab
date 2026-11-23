<!-- built by grader.build_sheet from reply-sheet-common.md and sqlglot/T1/replies.md -->
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

## T1-other-dialects-question
When: The developer asks whether T-SQL, Teradata or Redshift should also accept `top` as a column name, or whether to change how those dialects read `TOP`, and has not changed them.
Reply: No, leave those three exactly as they are. They have a real `TOP` clause, `TOP (expr)` and bind parameters included. Only Snowflake and Oracle are part of this.

## T1-other-dialects-changed
When: The developer reports having changed, or states as settled that it will change, how T-SQL, Teradata or Redshift read `TOP`, and is not asking whether that is acceptable.
Rescue: yes
Reply: Please undo the change to those dialects. T-SQL, Teradata and Redshift have a real `TOP` clause and must behave exactly as before, `TOP (expr)` and `TOP %s` included. Only Snowflake and Oracle are part of this.

## T1-parentheses
When: The developer asks what `top(...)` or `TOP (...)` with parentheses should mean in Snowflake or Oracle.
Reply: A function call, written back as it came in. In Snowflake only `TOP` followed directly by a plain number is a row limit; Oracle has no `TOP` clause at all.

## T1-top-number
When: The developer asks whether `SELECT TOP 5 x FROM t` should keep working in Snowflake, or how it should be written out.
Reply: Yes, it stays a row limit and is still written as `SELECT x FROM t LIMIT 5`.
