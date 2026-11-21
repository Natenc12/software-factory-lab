# T1 replies (stand-in owner)

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
