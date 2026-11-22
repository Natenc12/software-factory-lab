# T9 replies (stand-in owner)

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
Reply: Not in this ticket. Only the current version and the incoming one.

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
