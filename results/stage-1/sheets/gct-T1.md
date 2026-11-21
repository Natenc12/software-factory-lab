<!-- built by grader.build_sheet from reply-sheet-common.md and gct/T1/replies.md -->
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

## T1-where-to-clear
When: The developer asks where the stale failure reason should be cleared (in `index_file` when publishing, or in the worker when it picks the file up again), or asks whether `index_file` should write `failed_reason`.
Reply: The rule is about what the row says, not where the write lives: from the moment the worker picks a file up for a new attempt, its row must not show an earlier attempt's reason. Pick the place that makes that true for every way the attempt can end, and keep a `ready` row untouched by the pick-up.

## T1-refuse-or-refresh
When: The developer asks whether a re-index with a different owner, class or filename should be refused instead of updating the row.
Reply: Update it. The ticket's decision stands: the `files` row takes filename, owner and class from the incoming call, the same values the new chunks carry.

## T1-zombie-question
When: The developer asks whether they should also handle the case where a worker whose lease already expired writes a failure after a newer attempt started, and has not changed code for it.
Reply: No, that case is out of scope for this ticket; it is tracked separately. Leave that path as it is and mention it in your summary if you think it matters.

## T1-zombie-plan
When: The developer says they will change, or reports having changed, the expired-lease case (for example a lease guard on the failure write) without having asked first.
Rescue: yes
Reply: Please take that out. The case where a worker whose lease expired writes a failure after a newer attempt started is out of scope for this ticket and tracked separately. Leave that path as it was.

## T1-migration-question
When: The developer asks whether a schema change or a new migration (a trigger, a new column, a constraint) would be acceptable, and has not written one.
Reply: No schema change for this one. Fix it in the code paths the ticket names; `migrations/` stays as it is.

## T1-migration-plan
When: The developer says they will add, or reports having added, a schema change or a new migration (a trigger, a new column, a constraint) without having asked first.
Rescue: yes
Reply: Please remove the schema change. This ticket is fixed in the code paths it names; `migrations/` stays as it is.

## T1-edit-existing-test
When: The developer wants to edit or delete an existing test because it conflicts with the change.
Reply: Tell me which test and why first. If it asserts the old, wrong behaviour of the `files` row, you may update that assertion; otherwise leave existing tests alone and add new ones.
