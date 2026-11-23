<!-- built by grader.build_sheet from reply-sheet-common.md and sqlglot/T7/replies.md -->
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

## T7-open-decision
When: The developer asks what to do with COALESCE arguments that come after a non-NULL literal (for example COALESCE(x, 0, y)), or proposes a rule for them and asks for confirmation, or lists options for it.
Reply: Drop them: nothing after a value that can never be NULL is ever reached. COALESCE(x, 0, y) becomes COALESCE(x, 0), COALESCE(x, 'a', NULL, y) becomes COALESCE(x, 'a'), and COALESCE(NULL, 0, y) becomes just 0.

## T7-opt-in
When: The developer asks whether the tidy-up should only run when coalesce_simplification=True, or proposes putting it behind that option or a new option.
Reply: No, it should happen in the default simplify() and so in optimize(), with or without coalesce_simplification. That option stays as it is for the comparison rewrite.

## T7-fixtures
When: The developer asks whether they may update existing expectations in tests/fixtures/optimizer/simplify.sql that still show NULL arguments inside COALESCE.
Reply: Yes, update those expectations to the new output; that's expected. Don't change any other expectations.

## T7-typed-null
When: The developer asks whether a typed NULL such as CAST(NULL AS INT) counts as a NULL argument to remove.
Reply: No, leave typed NULLs alone; only a bare NULL literal is removed.

## T7-transpile
When: The developer asks whether transpile() without the optimizer should also drop NULL arguments.
Reply: No. Plain transpiling writes COALESCE exactly as given; only the optimizer tidies it up.

## T7-result-type
When: The developer points out that dropping the arguments after a non-NULL literal can change the type of the result (for example COALESCE(int_col, 0, 1.5)), or asks whether to drop them only when the types are known to match.
Reply: Either is fine with me: always drop them, or drop them only when that cannot change the result type. What I need is that optimize() with a schema drops them when the columns and the constant have the same type, so COALESCE(a, 0, b) on INT columns becomes COALESCE(a, 0).
