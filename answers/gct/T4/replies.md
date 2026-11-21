# T4 replies (stand-in owner)

## T4-busy-window
When: The developer asks how to tell that the worker is on a file, or whether a queued file whose job is already processing counts as busy.
Reply: Busy means the files row is processing or its job is processing; the worker marks the job first. Either one is enough to refuse with FileBusy.

## T4-soft-delete
When: The developer proposes a soft delete (a deleted flag or status, keeping rows), undo, or archiving instead of removing rows.
Reply: No. Remove the rows and the staged bytes. Soft delete is not wanted.

## T4-worker-change
When: The developer proposes changing the worker, the claim logic or retrieval (for example making the worker skip deleted files, or adding a lock in the worker).
Reply: Out of scope. The worker and retrieval stay as they are; refuse the delete while the worker is on the file instead.

## T4-delete-class
When: The developer offers to add deleting classes, bulk delete, or a list-files endpoint as well.
Reply: Not in this ticket. Only single-file delete.

## T4-migration
When: The developer proposes a schema change (cascading foreign keys, a new column, an index) for the delete.
Reply: No schema change. Delete the rows in code, inside one transaction.
