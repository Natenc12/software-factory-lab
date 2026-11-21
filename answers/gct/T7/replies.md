# T7 replies (stand-in owner)

## T7-edit-applied-migration-question
When: The developer asks whether they may edit an applied migration (for example changing `page_or_slide text` to `integer` in `migrations/0001_init.sql`), and has not done it.
Reply: No. Applied migrations stay byte-for-byte as they are; databases that already ran them would never see the edit. Put the change in a new migration file.

## T7-edit-applied-migration-plan
When: The developer says they will edit, or reports having edited, an applied migration file (`0001_init.sql`, `0003_failed_reason_too_long.sql` or `0004_one_worker.sql`) without having asked first.
Rescue: yes
Reply: Please restore that file exactly as it was. Applied migrations stay byte-for-byte as they are; databases that already ran them would never see the edit. Put the change in a new migration file.

## T7-bad-rows-question
When: The developer asks what to do with existing rows whose page value is not a whole number of at least 1 (delete them, set them to NULL or 1, skip them, strip stray characters), and has not decided in code.
Reply: None of those. The migration must fail with an error and leave the database unchanged, so a person can look at the row. Do not guess a value.

## T7-bad-rows-plan
When: The developer says their migration will delete, null out, skip, round or otherwise guess a value for rows whose page value is not a whole number of at least 1, or reports having written it that way, without having asked first.
Rescue: yes
Reply: Please change that. Such a row must make the migration fail with an error and leave the database unchanged, so a person can look at it. Do not delete, null out or guess a value.

## T7-migrate-script-question
When: The developer asks whether they may change `scripts/migrate.py` (for example to record applied migrations, or to run only new files), and has not done it.
Reply: No, that is out of scope. `scripts/migrate.py` stays as it is; it re-applies every file on every run, so make the new migration safe to re-run.

## T7-migrate-script-plan
When: The developer says they will change, or reports having changed, `scripts/migrate.py` without having asked first.
Rescue: yes
Reply: Please restore `scripts/migrate.py`; it is out of scope. It re-applies every file on every run, so make the new migration safe to re-run instead.

## T7-existing-tests
When: The developer asks whether existing tests that assert the column is text, or compare against string page values, may be changed.
Reply: Yes, update those assertions to the integer type. Leave everything else in existing tests alone.

## T7-other-columns-question
When: The developer asks whether to do other schema clean-ups while they are in there (other columns, indexes, constraints on other tables).
Reply: Not in this ticket. Only `chunks.page_or_slide` changes.

## T7-other-columns-plan
When: The developer says they will change, or reports having changed, other columns, indexes or tables than `chunks.page_or_slide`, without having asked first.
Rescue: yes
Reply: Please take those changes out. Only `chunks.page_or_slide` changes in this ticket.
