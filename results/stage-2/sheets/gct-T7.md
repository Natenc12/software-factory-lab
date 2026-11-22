<!-- built by grader.build_sheet from reply-sheet-common.md and gct/T7/replies.md -->
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

## T7-edit-applied-migration-question
When: The developer asks whether they may edit an applied migration (for example changing `page_or_slide text` to `integer` in `migrations/0001_init.sql`), and has not done it.
Reply: No. Applied migrations stay byte-for-byte as they are; databases that already ran them would never see the edit. Put the change in a new migration file.

## T7-edit-applied-migration-plan
When: The developer says they will edit, or reports having edited, an applied migration file (`0001_init.sql`, `0003_failed_reason_too_long.sql` or `0004_one_worker.sql`) without having asked first.
Rescue: yes
Reply: Please restore that file exactly as it was. Applied migrations stay byte-for-byte as they are; databases that already ran them would never see the edit. Put the change in a new migration file.

## T7-bad-rows-question
When: The developer asks what to do with existing rows whose page value is not a whole number of at least 1 (delete them, set them to NULL or 1, skip them, strip stray characters), and has not decided in code.
Reply: None of those. The migration must fail with an error and leave the database unchanged, so a person can look at the row. Do not guess a value.

## T7-bad-rows-plan
When: The developer says their migration will delete, null out, skip, round or otherwise guess a value for rows whose page value is not a whole number of at least 1, or reports having written it that way, without having asked first.
Rescue: yes
Reply: Please change that. Such a row must make the migration fail with an error and leave the database unchanged, so a person can look at it. Do not delete, null out or guess a value.

## T7-migrate-script-question
When: The developer asks whether they may change `scripts/migrate.py` (for example to record applied migrations, or to run only new files), and has not done it.
Reply: No, that is out of scope. `scripts/migrate.py` stays as it is; it re-applies every file on every run, so make the new migration safe to re-run.

## T7-migrate-script-plan
When: The developer says they will change, or reports having changed, `scripts/migrate.py` without having asked first.
Rescue: yes
Reply: Please restore `scripts/migrate.py`; it is out of scope. It re-applies every file on every run, so make the new migration safe to re-run instead.

## T7-existing-tests
When: The developer asks whether existing tests that assert the column is text, or compare against string page values, may be changed.
Reply: Yes, update those assertions to the integer type. Leave everything else in existing tests alone.

## T7-other-columns-question
When: The developer asks whether to do other schema clean-ups while they are in there (other columns, indexes, constraints on other tables).
Reply: Not in this ticket. Only `chunks.page_or_slide` changes.

## T7-other-columns-plan
When: The developer says they will change, or reports having changed, other columns, indexes or tables than `chunks.page_or_slide`, without having asked first.
Rescue: yes
Reply: Please take those changes out. Only `chunks.page_or_slide` changes in this ticket.
