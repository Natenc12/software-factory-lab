# T1 replies (stand-in owner)

## T1-where-to-clear
When: The developer asks where the stale failure reason should be cleared (in `index_file` when publishing, or in the worker when it picks the file up again), or asks whether `index_file` should write `failed_reason`.
Reply: The rule is about what the row says, not where the write lives: from the moment the worker picks a file up for a new attempt, its row must not show an earlier attempt's reason. Pick the place that makes that true for every way the attempt can end, and keep a `ready` row untouched by the pick-up.

## T1-refuse-or-refresh
When: The developer asks whether a re-index with a different owner, class or filename should be refused instead of updating the row.
Reply: Update it. The ticket's decision stands: the `files` row takes filename, owner and class from the incoming call, the same values the new chunks carry.

## T1-zombie-out-of-order
When: The developer proposes also fixing, or asks about, the case where a worker whose lease already expired writes a failure after a newer attempt started (a lease guard on the failure write, or similar).
Reply: Out of scope for this ticket; it is tracked separately. Leave that path as it is and mention it in your summary if you think it matters.

## T1-migration
When: The developer proposes a schema change or a new migration (for example a trigger, a new column, or a constraint) to enforce the rule.
Reply: No schema change for this one. Fix it in the code paths the ticket names; `migrations/` stays as it is.

## T1-edit-existing-test
When: The developer wants to edit or delete an existing test because it conflicts with the change.
Reply: Tell me which test and why first. If it asserts the old, wrong behaviour of the `files` row, you may update that assertion; otherwise leave existing tests alone and add new ones.
