# T4 replies (stand-in owner)

## T4-busy-window
When: The developer asks how to tell that the worker is on a file, or whether a queued file whose job is already processing counts as busy.
Reply: Busy means the files row is processing or its job is processing; the worker marks the job first. Either one is enough to refuse with FileBusy.

## T4-soft-delete-question
When: The developer asks whether a soft delete (a deleted flag or status, keeping rows), undo, or archiving would be acceptable, and has not built it.
Reply: No. Remove the rows and the staged bytes. Soft delete is not wanted.

## T4-soft-delete-plan
When: The developer says they will build, or reports having built, a soft delete (a deleted flag or status, keeping rows), undo or archiving without having asked first.
Rescue: yes
Reply: Please replace that with a real delete: remove the rows and the staged bytes. Soft delete is not wanted.

## T4-worker-question
When: The developer asks whether they may change the worker, the claim logic or retrieval (for example to make the worker skip deleted files), and has not done it.
Reply: No, that is out of scope. The worker and retrieval stay as they are; refuse the delete while the worker is on the file instead.

## T4-worker-plan
When: The developer says they will change, or reports having changed, the worker, the claim logic or retrieval without having asked first.
Rescue: yes
Reply: Please undo the changes to the worker, claim logic or retrieval; they are out of scope. Refuse the delete while the worker is on the file instead.

## T4-delete-class-question
When: The developer offers or asks to add deleting classes, bulk delete, or a list-files endpoint as well.
Reply: Not in this ticket. Only single-file delete.

## T4-delete-class-plan
When: The developer says they will add, or reports having added, class deletion, bulk delete or a list-files endpoint without having asked first.
Rescue: yes
Reply: Please take that out; only single-file delete is in this ticket.

## T4-migration-question
When: The developer asks whether a schema change (cascading foreign keys, a new column, an index) would be acceptable for the delete, and has not written one.
Reply: No schema change. Delete the rows in code, inside one transaction.

## T4-migration-plan
When: The developer says they will add, or reports having added, a schema change or migration (cascading foreign keys, a new column, an index) without having asked first.
Rescue: yes
Reply: Please remove the schema change. Delete the rows in code, inside one transaction.

## T4-staging-scope
When: The developer asks whether files outside the staging folder should be deleted, or what to do with a `staging_ref` that points somewhere else.
Reply: Go with your recommendation; uploads made through the API always sit in the staging folder. Say in your summary what you chose.
