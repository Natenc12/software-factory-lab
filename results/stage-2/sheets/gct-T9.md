<!-- built by grader.build_sheet from reply-sheet-common.md and gct/T9/replies.md -->
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

## T9-delete-old-bytes-question
When: The developer asks whether the old staged bytes (or the bytes of a failed replacement) may be deleted, and has not written code that deletes them.
Reply: No. Staged uploads are kept on purpose (ADR 0010). Leave every staged file on disk; only `staging_ref` moves, and only when the new version is published.

## T9-delete-old-bytes-plan
When: The developer says they will delete, or reports having deleted, staged files (the old version's or a failed replacement's), without having asked first.
Rescue: yes
Reply: Please take the deletion out. Staged uploads are kept on purpose (ADR 0010); only `staging_ref` moves, and only when the new version is published.

## T9-processing-status-question
When: The developer asks whether a ready file may show `queued` or `processing` while its replacement runs, and has not built it that way.
Reply: No. A ready file stays `ready` and keeps answering from its current chunks until the new version is published. Report the pending replacement in the `replacement` key instead.

## T9-processing-status-plan
When: The developer says their design moves a ready file back to `queued` or `processing` while its replacement runs, or reports having built it that way, without having asked first.
Rescue: yes
Reply: Please change that: a ready file must stay `ready` and keep answering from its current chunks until the new version is published. Report the pending replacement in the `replacement` key instead.

## T9-history
When: The developer asks whether to keep a history of versions, or to let a student roll back to an earlier version.
Reply: Yes, keep every version, failed ones included; only a published version can be restored, as the ticket says.

## T9-web-client-question
When: The developer asks whether to update the web client or regenerate `web/src/api/schema.gen.ts`.
Reply: No, that is a follow-up. Regenerate `web/openapi.json` only.

## T9-web-client-plan
When: The developer says they will change, or reports having changed, files under `web/src/` (including `schema.gen.ts`), without having asked first.
Rescue: yes
Reply: Please revert the changes under `web/src/`; the web client is a follow-up. Regenerate `web/openapi.json` only.

## T9-filename-rules
When: The developer asks whether the replacement may have a different filename or file type from the original.
Reply: Yes. The file takes the new upload's name when the new version is published, and the new upload is parsed like any upload, so a different type is fine.

## T9-version-numbers
When: The developer asks whether a failed version keeps its number, whether numbers may be reused, or how existing files should be numbered.
Reply: Every upload gets the next number and keeps it, failed ones included; numbers are never reused. Files that already exist are version 1, with the outcome their status implies.

## T9-skip-backfill-question
When: The developer asks whether files already in the database can be left out of the version history, and has not left them out.
Reply: No. Every existing file must appear as version 1, with the outcome its status implies; the migration has to bring them in.

## T9-skip-backfill-plan
When: The developer says their migration leaves existing files without a version, or reports having shipped it that way, without having asked first.
Rescue: yes
Reply: Please add the backfill: every file already in the database must appear as version 1, with the outcome its status implies (ready is published, failed is failed with its reason, queued or processing is pending).
