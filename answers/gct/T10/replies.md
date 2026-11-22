# T10 replies (stand-in owner)

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
