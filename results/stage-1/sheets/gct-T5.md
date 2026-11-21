<!-- built by grader.build_sheet from reply-sheet-common.md and gct/T5/replies.md -->
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

## T5-open-decision
When: The developer asks what counts as the same class name (case, spaces, punctuation, accents), or proposes a comparison rule and asks for confirmation, or lists options for it.
Reply: Two names are the same when they match after trimming whitespace at both ends, collapsing every run of whitespace inside (spaces, tabs, newlines) to a single space, and ignoring letter case. Everything else counts: punctuation, digits and accents. So "Biology 101", "biology 101", "  BIOLOGY   101 " and "Biology\t101" are one name; "Biology-101", "Biology101" and "Biologie 101" are different. Keep storing the name exactly as typed.

## T5-unique-index
When: The developer asks whether to enforce the rule with a unique index or constraint in a new migration.
Reply: Only if it cannot fail on existing data. Some owners already have duplicate classes and those must stay as they are, so deploying cannot depend on there being none. Checking in create_class is fine.

## T5-existing-duplicates-question
When: The developer asks what to do with classes that already share a name, without having changed them.
Reply: Leave them exactly as they are. The rule only applies when a new class is created.

## T5-existing-duplicates-plan
When: The developer says they will merge, rename or delete classes that already share a name (in code or in a migration), or reports having done so, without having asked first.
Rescue: yes
Reply: Please undo that. Existing classes stay exactly as they are; the rule only applies when a new class is created.

## T5-reason-set-question
When: The developer asks whether to add a new reason to ClassNameError / CLASS_NAME_REASONS for the duplicate case.
Reply: No, use a separate ClassNameTaken exception as the ticket says; the reason set is closed and pinned by tests, and a duplicate is a 409, not a 400.

## T5-reason-set-plan
When: The developer says they will add, or reports having added, a new reason to ClassNameError / CLASS_NAME_REASONS without having asked first.
Rescue: yes
Reply: Please revert that and use a separate ClassNameTaken exception, as the ticket says. The reason set is closed and pinned by tests, and a duplicate is a 409, not a 400.

## T5-rename-list-question
When: The developer offers or asks to add renaming or listing classes as well.
Reply: Not in this ticket.

## T5-rename-list-plan
When: The developer says they will add, or reports having added, renaming or listing classes without having asked first.
Rescue: yes
Reply: Please take that out; renaming and listing classes are not part of this ticket.
