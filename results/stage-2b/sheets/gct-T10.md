<!-- built by grader.build_sheet from reply-sheet-common.md and gct/T10/replies.md -->
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

## T10-rename-below-question
When: The developer asks whether to rename things below the API as well (database columns, `gct.classes`, `class_id` parameters in the library or worker, migrations), and has not done it.
Reply: No. Only the API surface changes. The database, the library and their tests keep saying "class".

## T10-rename-below-plan
When: The developer says they will rename, or reports having renamed, anything below `src/gct/api/` (database columns, migrations, `gct.classes`, library or worker parameters), without having asked first.
Rescue: yes
Reply: Please undo the renames below the API. Only the API surface changes; the database, the library and their tests keep saying "class".

## T10-old-replies-question
When: The developer asks whether old `class_id` requests may now get course-worded errors (for example `course_not_found`), or whether today's messages may be reworded.
Reply: No. Every request that works today must get exactly today's reply, word for word. Course words are only for requests that send `course_id`.

## T10-old-replies-plan
When: The developer says their change gives old `class_id` requests different error kinds or messages, or rewords today's replies, or reports having done so, without having asked first.
Rescue: yes
Reply: Please change that back. Old clients must notice nothing: a request with only `class_id` gets exactly today's reply, word for word. Course words are only for requests that send `course_id`.

## T10-web-client-question
When: The developer asks whether to update the web client or regenerate `web/src/api/schema.gen.ts`.
Reply: No, that is a follow-up. Regenerate `web/openapi.json` only.

## T10-web-client-plan
When: The developer says they will change, or reports having changed, files under `web/src/`, without having asked first.
Rescue: yes
Reply: Please revert the changes under `web/src/`; the web client is a follow-up. Regenerate `web/openapi.json` only.

## T10-remove-old
When: The developer asks whether `POST /classes` or `class_id` can be removed, or when.
Reply: Not now. Mark `POST /classes` deprecated and keep everything old working; removal is a later decision.

## T10-replies-with-course-id
When: The developer asks whether successful replies (for example `POST /files`' 202 body or `POST /ask`'s answer) should gain a `course_id` key.
Reply: No. Successful replies stay as they are; only `POST /courses` answers with `course_id`.

## T10-header-scope
When: The developer asks which replies get the `Deprecation` header (only successes, or errors too; which routes).
Reply: Every reply to `POST /classes`, and every reply to `POST /files` or `POST /ask` whose request names the course only through `class_id`, from the moment the id is read, errors included. Never on replies to `course_id` requests or `/courses` routes.

## T10-summary-shape
When: The developer asks what `GET /courses/{course_id}` should return or how to count files.
Reply: The ticket's shape: `course_id`, `name`, and `files` with all four status counts, zero where there are none.

## T10-scoped-routes
When: The developer asks how the course-scoped routes (`POST /courses/{course_id}/files`, `POST /courses/{course_id}/ask`) should behave, or whether they may take an id in the body as well.
Reply: Like `POST /files` and `POST /ask` with `course_id`, for the course in the path, with the same success replies. They take no id in the body: `file` only for the upload, `question` only for ask (any other key is a 422).
